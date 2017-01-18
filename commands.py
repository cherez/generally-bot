commands = {}
import db
from sqlalchemy.exc import IntegrityError

def command(func):
    commands[func.__name__] = func
    return func


@command
def help(connection, event, body):
    '''Lists commands and usage'''
    if not body:
        choices = sorted(commands.keys(), reverse=True)
    else:
        choices = body.split()

    for choice in choices:
        if choice not in commands:
            connection.say(choice + ' not found')
            continue
        command = commands[choice]
        message = '{:20s} -- {}'.format(choice, command.__doc__)

        connection.say(message)

@command
def add(connection, event, body):
    args = body.split(maxsplit = 1)
    if len(args) < 2:
        connection.say('Usage: !add [list] [value]')
        return
    target = args[0]
    body = args[1]
    session = connection.db()
    if target == 'list':
        if len(body.split()) > 1:
            connection.say('Usage: !add list [single word list name]')
            return
        lists = session.query(db.List).filter(db.List.name == body).all()
        dicts = session.query(db.Dict).filter(db.Dict.name == body).all()
        if lists or dicts:
            connection.say(body + "already exists.")
            return
        if add(session, db.List, name = body):
            connection.say('Added List ' + body)
        return

    if target == 'dict':
        if len(body.split()) > 1:
            connection.say('Usage: !add dict [single word dict name]')
            return
        lists = session.query(db.List).filter(db.List.name == body).all()
        dicts = session.query(db.Dict).filter(db.Dict.name == body).all()
        if lists or dicts:
            connection.say(body + "already exists.")
            return
        if add(session, db.Dict, name = body):
            connection.say('Added Dict ' + body)
        else:
            connection.say('Dict ' + body + ' already exists.')
        return

    lists = session.query(db.List).filter(db.List.name == target).all()
    dicts = session.query(db.Dict).filter(db.Dict.name == target).all()

    print(lists)
    if lists:
        if add(session, db.ListItem, list=target, value = body):
            connection.say('Added ' + body + ' to ' + target)
        else:
            connection.say(body + ' is already in ' + target + '.')
        return

    print(dicts)
    if dicts:
        if len(body.split()) < 2:
            connection.say('Usage: !add " {} [key] [value]'.format(target))
            return
        name, value = body.split(maxsplit = 1)
        if add(session, db.DictItem, dict = target, name = name, value = value):
            connection.say('Added ' + name + ' to ' + target)
        else:
            connection.say(name + 'already exists in ' + target)
        return
    connection.say("I don't know what a " + target + " is.")


def add(session, table, **values):
    try:
        session.add(table(**values))
        session.commit()
        return True
    except IntegrityError:
        return False
