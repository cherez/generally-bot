import logging.handlers
import os
import textwrap
import time

from handlers import handle

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
os.makedirs('logs', exist_ok=True)
output = logging.handlers.TimedRotatingFileHandler('logs/chat.log', 'D')
formatter = logging.Formatter("%(message)s")
output.setFormatter(formatter)
output.setLevel(logging.DEBUG)
logger.addHandler(output)

wrapper = textwrap.TextWrapper()
wrapper.subsequent_indent = '      '

@handle('pubmsg')
def on_pubmsg(connection, event):
    source = event.source.nick
    message = event.arguments[0]
    log("{}: {}".format(source, message))

@handle('say')
def on_say(connection, event):
    source = connection.nick
    message = event.arguments[0]
    log("{}: {}".format(source, message))

def log(message):
    now = time.strftime("%H:%M:%S ")
    lines = wrapper.wrap(now + message)
    for line in lines:
        logger.info(line)
