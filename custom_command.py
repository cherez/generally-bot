import db
from template import render

def find(connection, name):
    session = connection.db()
    result = session.query(db.DictItem).filter(db.DictItem.dict == 'command').filter(db.DictItem.name == name).all()
    if not result:
        return None
    template = result[0].value
    def reader(connection, event, body):
        connection.say(render(session, template))
    return reader
