from handlers import handle
from config import config

greeting = config.get('greeting')

#don't greet if no greeting is set
if greeting:
    @handle('new-users')
    def greet(connection, event):
        for user in event.arguments:
            connection.say(greeting.format(name=user.name))
