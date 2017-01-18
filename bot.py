import irc.bot
import irc.strings
from irc.client import ip_numstr_to_quad, ip_quad_to_numstr
import ssl
import commands
import db
import traceback
import threading
import collections
import time
import custom_command
import schedules
from schedules import every
import requests

class Bot(irc.bot.SingleServerIRCBot):
    def __init__(self, config):
        self.config = config
        self.channel = config['chan']
        nick = config['name']
        password = config['pass']
        server = config['server']
        port = config['port']
        server = [(server, port, password)]
        self.db = db.init(self.channel)
        irc.bot.SingleServerIRCBot.__init__(self, server, nick, nick)
        self.chat_queue = collections.deque()

    def on_welcome(self, c, e):
        print('Welcomed! Joining ' + self.channel)
        c.join(self.channel)
        self._start_schedules()

    def on_privmsg(self, c, e):
        print('privmsg')

    def on_pubmsg(self, c, event):
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
        try:
            message = function(self, event, body)
            if message:
                self.say(message)
        except:
            self.say("Error! Yell at Break to fix it!")
            print(traceback.format_exc())

    def say(self, message):
        print("Saying " + message)
        self.chat_queue.append(message)

    def _process_chat_queue(self):
        if len(self.chat_queue) > 0:
            message = self.chat_queue.pop()
            print("Sending " + message)
            self.connection.privmsg(self.channel, message)

    def _start_schedules(self):
        for schedule in schedules.schedules:
            self.reactor.execute_every(schedule.delay, schedule.function, [self])
            self.reactor.execute_at(0, schedule.function, [self])

    def find_command(self, command):
        function = commands.commands.get(command)
        if not function:
            function = custom_command.find(self, command)
        if not function:
            def missing(connection, event, body):
                connection.say("Command {} not found.".format(command))
            return missing
        return function


    def get_users(self):
        channel = self.channel[1:] #strip the leading # from the IRC channel
        url = 'http://tmi.twitch.tv/group/user/{}/chatters'.format(channel)
        try:
            r = requests.get(url)
            data = r.json()
            if data: #sometimes this just fails :/
                self.user_data = r.json()
                #toss this in the reactor to keep DB stuff in the main thread
                self.reactor.execute_at(0, self.update_users)
        except ValueError:
            return None
        except TypeError:
            return None

    def update_users(self):
        print("Updating users")
        users = self.user_data['chatters']
        session = self.db()
        for mod in users['moderators']:
            user = db.find_or_make(session, db.User, name=mod)
            user.mod = True
        for viewer in users['viewers']:
            user = db.find_or_make(session, db.User, name=viewer)
            user.mod = False
        session.commit()

@every(60)
def update_users(connection):
    #background this to not block
    thread = threading.Thread(target = connection.get_users)
    thread.daemon = True
    thread.start()

@every(1)
def chat(connection):
    connection._process_chat_queue()
