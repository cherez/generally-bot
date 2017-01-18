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
    '''Creates a value.'''
    args = body.split(maxsplit = 1)
    if len(args) < 2:
        return 'Usage: !add [type] [value]'
    target = args[0]
    body = args[1]
    session = connection.db()
    if target in ['list', 'dict']:
        if len(body.split()) > 1:
            return 'Usage: !add {} [single word list name]'.format(target)
        lists = db.find(session, db.List, name=body).all()
        dicts = db.find(session, db.Dict, name=body).all()
        if lists or dicts:
            return "{} {} already exists.".format((lists+dicts)[0].__class__.__name__, body)
        type = db.List if target=='list' else db.Dict
        db.add(session, type, name = body)
        return 'Added {} {}'.format(target, body)

    lists = db.find(session, db.List, name=target).all()
    dicts = db.find(session, db.Dict, name=target).all()

    if lists:
        if db.add(session, db.ListItem, list=target, value = body):
            return 'Added ' + body + ' to ' + target
        return body + ' is already in ' + target + '.'

    if dicts:
        if len(body.split()) < 2:
            return 'Usage: !add " {} [key] [value]'.format(target)
        name, value = body.split(maxsplit = 1)
        if db.add(session, db.DictItem, dict = target, name = name, value = value):
            return 'Added ' + name + ' to ' + target
        else:
            db.find(session, db.DictItem, dict=target, name=name) \
                .update({db.DictItem.value: value})
            session.commit()
            return "{} updated to {}".format(name, value)
    return "I don't know what a " + target + " is."

@command
def remove(connection, event, body):
    '''Deletes a value.'''
    args = body.split(maxsplit = 1)
    if len(args) < 2:
        return 'Usage: !remove [type] [value]'
    target = args[0]
    body = args[1]
    session = connection.db()
    if target == 'list':
        if not db.remove(session, db.List, name=body):
            return "List {} does not exist.".format(body)
        return "Removed list {}.".format(target)

    if target == 'dict':
        if not db.remove(session, db.Dict, name=body):
            return "Dict {} does not exist.".format(body)
        return "Removed dict {}.".format(target)

    lists = db.find(session, db.List, name=target).all()
    dicts = db.find(session, db.Dict, name=target).all()

    if lists:
        if not db.remove(session, db.ListItem, list=target, value=body):
            return "{} not in {}.".format(body, target)
        return "Removed {} from {}.".format(body, target)

    if dicts:
        if not db.remove(session, db.DictItem, dict=target, key=body):
            return "{} not in {}.".format(body, target)
        return "Removed {} from {}.".format(body, target)
    return "I don't know what a " + target + " is."

