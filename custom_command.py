import db
import re
import random

pattern = re.compile('\[[^\]]*\]')

def find(connection, name):
    session = connection.db()
    result = session.query(db.DictItem).filter(db.DictItem.dict == 'command').filter(db.DictItem.name == name).all()
    if not result:
        return None
    message = result[0].value
    def reader(connection, event, body):
        connection.say(read(session, message))
    return reader

def read(session, message):
    patterns = pattern.findall(message)
    for match in patterns:
        list = match[1:-1]
        items = session.query(db.ListItem).filter(db.ListItem.list == list).all()
        if items:
            message = message.replace(match, random.choice(items).value, 1)
    return message
