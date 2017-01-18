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
        self.chat_thread = threading.Thread(target=self._process_chat_queue,
                kwargs={'chat_queue': self.chat_queue})
        self.chat_thread.daemon = True
        self.chat_thread.start()


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
            function(self, event, body)
        except:
            self.say("Error! Yell at Break to fix it!")
            print(traceback.format_exc())

    def say(self, message):
        print("Saying " + message)
        self.chat_queue.append(message)

    def _process_chat_queue(self, chat_queue):
        """
        If there are messages in the chat queue that need
        to be sent, pop off the oldest one and pass it
        to the ts.send_message function. Then sleep for
        half a second to stay below the twitch rate limit.
        """
        while True:
            if len(chat_queue) > 0:
                message = chat_queue.pop()
                print("Sending " + message)
                self.connection.privmsg(self.channel, message)
            time.sleep(1)


    def find_command(self, command):
        function = commands.commands.get(command)
        if not function:
            function = custom_command.find(self, command)
        if not function:
            def missing(connection, event, body):
                connection.say("Command {} not found.".format(command))
            return missing
        return function

