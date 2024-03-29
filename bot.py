import asyncio
from datetime import datetime

import aiohttp
import irc.bot
import irc.strings
from irc.client import ip_numstr_to_quad, ip_quad_to_numstr, Event
import ssl
import commands
import db
import traceback
import threading
import collections
import time
import custom_command
import schedules
from schedules import every, background
import requests
import modules
import handlers


class Bot(irc.bot.SingleServerIRCBot):
    def __init__(self, config):
        self.config = config
        self.channel = config['chan']
        self.nick = config['name']
        password = config['pass']
        server = config['server']
        port = config['port']
        server = [(server, port, password)]
        self.db = db.init(self.channel)
        ssl_factory = irc.connection.Factory(wrapper=ssl.wrap_socket)
        self.chat_queue = collections.deque()
        self.start_loop()
        irc.bot.SingleServerIRCBot.__init__(self, server,
                                            self.nick, self.nick,
                                            connect_factory=ssl_factory)
        for type, funcs in handlers.handlers.items():
            for func in funcs:
                self.reactor.add_global_handler(type, func, 0)

    def on_welcome(self, c, e):
        print('Welcomed! Joining ' + self.channel)
        c.join(self.channel)
        # launch the start event before schedules to give modules a chance to initialize
        self.handle_event(Event('bot-start', self.nick, self.channel))
        self._start_schedules()

    def on_privmsg(self, c, e):
        print('privmsg')

    def on_pubmsg(self, c, event):
        print('pubmsg')
        command = event.arguments[0]
        self.do_command(event, command)
        return

    def do_command(self, event, cmd):
        source = event.source.nick
        print("{}: {}".format(source, cmd))

        if cmd[0] != '!':
            return
        cmd = cmd[1:]
        if cmd == '':
            cmd = 'help'

        args = cmd.split(maxsplit=1)
        if len(args) > 1:
            cmd = args[0]
            body = args[1]
        else:
            body = ''

        function = self.find_command(cmd)
        self.run_action(function(self, event, body))

    def say(self, message):
        print("Saying " + message)
        self.chat_queue.append(message)

    def _process_chat_queue(self):
        if len(self.chat_queue) > 0:
            message = self.chat_queue.popleft()
            print("Sending " + message)
            self.connection.privmsg(self.channel, message)
            event = Event('say', self.nick, self.channel, [message])
            self.reactor._handle_event(self, event)

    def _start_schedules(self):
        for schedule in schedules.schedules:
            print(schedule.function.__name__)
            self.reactor.scheduler.execute_every(schedule.delay, lambda: schedule.function(self))
            self.reactor.scheduler.execute_after(0, lambda: schedule.function(self))

        for task in schedules.background_tasks:
            self.run_action(task(self))

    def find_command(self, command):
        command = command.replace('_', '-').lower()
        function = commands.commands.get(command)
        if not function:
            function = commands.aliases.get(command)
        if not function:
            function = custom_command.find(self, command)
        if not function:
            def missing(connection, event, body):
                connection.say("Command {} not found.".format(command))

            return missing
        return function

    async def get_users(self):
        channel = self.channel[1:]  # strip the leading # from the IRC channel
        url = 'http://tmi.twitch.tv/group/user/{}/chatters'.format(channel)
        try:
            async with self.session.get(url) as r:
                data = await r.json()
                if data:  # sometimes this just returns None :/
                    self.user_data = data
                    self.update_users()
        except (aiohttp.ClientError, asyncio.TimeoutError):
            # Server sometimes fails; carry on
            return None

    def update_users(self):
        users = self.user_data['chatters']
        new = []
        all_users = []
        for name in users['moderators'] + users['viewers']:
            user = db.find_or_make(db.User, name=name)
            user.mod = name in users['moderators']
            all_users.append(user)
            if user._new:
                print(f"{datetime.now().isoformat()} New user!: {name}")
                new.append(user)
        db.db.save()
        if new:
            event = Event('new-users', self.channel, self.channel, new)
            self.reactor._handle_event(self, event)
        event = Event('users', self.channel, self.channel, all_users)
        self.reactor._handle_event(self, event)

    def handle_event(self, event, source=None, target=None, body=[]):
        if not isinstance(event, Event):
            event = Event(event, source, target, body)
        self.reactor._handle_event(self, event)

    def start_loop(self):
        self.loop = asyncio.get_event_loop()
        self.session = aiohttp.ClientSession(loop=self.loop)
        thread = threading.Thread(target=self.loop.run_forever)
        thread.daemon = True
        thread.start()

    def run_action(self, coro):
        async def wrapper():
            try:
                if asyncio.iscoroutine(coro):
                    message = await coro
                else:
                    message = coro
                if message:
                    self.say(message)
            except:
                traceback.print_exc()
                self.say("Error in {} ! Yell at Break to fix it!".format(coro.__name__))

        asyncio.run_coroutine_threadsafe(wrapper(), self.loop)


@background
async def update_users(connection):
    while True:
        await connection.get_users()
        await asyncio.sleep(60)


@every(.5)
def chat(connection):
    connection._process_chat_queue()
