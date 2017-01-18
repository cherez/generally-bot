commands = {}
import db

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
    if target in ['list', 'dict']:
        if len(body.split()) > 1:
            connection.say('Usage: !add {} [single word list name]'.format(target))
            return
        lists = db.find(session, db.List, name=body).all()
        dicts = db.find(session, db.Dict, name=body).all()
        if lists or dicts:
            connection.say("{} {} already exists.".format((lists+dicts)[0].__class__.__name__, body))
            return
        type = db.List if target=='list' else db.Dict
        if db.add(session, type, name = body):
            connection.say('Added {} {}'.format(target, body))
        return

    lists = db.find(session, db.List, name=target).all()
    dicts = db.find(session, db.Dict, name=target).all()

    if lists:
        if db.add(session, db.ListItem, list=target, value = body):
            connection.say('Added ' + body + ' to ' + target)
        else:
            connection.say(body + ' is already in ' + target + '.')
        return

    if dicts:
        if len(body.split()) < 2:
            connection.say('Usage: !add " {} [key] [value]'.format(target))
            return
        name, value = body.split(maxsplit = 1)
        if db.add(session, db.DictItem, dict = target, name = name, value = value):
            connection.say('Added ' + name + ' to ' + target)
        else:
            db.find(session, db.DictItem, dict=target, name=name) \
                .update({db.DictItem.value: value})
            session.commit()
            connection.say("{} updated to {}".format(name, value))
        return
    connection.say("I don't know what a " + target + " is.")

