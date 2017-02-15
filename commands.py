commands = {}
import db
from functools import wraps

def command(func):
    name = func.__name__.replace('_', '-')
    commands[name] = func
    return func

def mod_only(func):
    @wraps(func)
    def restricted(connection, event, body):
        session = connection.db()
        nick = event.source.nick
        if not db.find(session, db.User, name=nick, mod=True).all():
            return "{} must be a mod to do that.".format(nick)
        return func(connection, event, body)
    if hasattr(restricted, 'long'):
        restricted.long = "MOD ONLY!\n" + restricted.long
    restricted.mod_only = True
    return restricted

def short(doc):
    def wrapper(func):
        func.short = doc
        return func
    return wrapper

def long(doc):
    def wrapper(func):
        func.long = doc
        return func
    return wrapper


@command
@short('Lists commands and usage')
@long('''!help
        Lists all available commands available to users with short descriptions
        !help [command ...]
        Gives detailed description of listed commands''')
def help(connection, event, body):
    if not body:
        choices = sorted(commands.items())
        for name, command in choices:
            #skip all commands
            if getattr(command, 'mod_only', False):
                continue
            short_help(connection, name, command)
    else:
        choices = body.split()

        for choice in choices:
            if choice not in commands:
                connection.say(choice + ' not found')
                continue
            command = commands[choice]
            long_help(connection, choice, command)

@command
@short('Lists mod-only commands and usage')
@long('''!help
        Lists all mod commands
        !help [command ...]
        Gives detailed description of listed commands''')
def mod_help(connection, event, body):
    choices = sorted(commands.items())
    for name, command in choices:
            if getattr(command, 'mod_only', False):
                short_help(connection, name, command)

def short_help(connection, name, command):
        doc = getattr(command, 'short', None) or getattr(command, '__doc__')
        message = '{:20s} -- {}'.format(name, doc)
        connection.say(message)

def long_help(connection, name, command):
        doc = getattr(command, 'long', None)
        if not doc:
            return short_help(connection, name, command)
        lines = doc.split('\n')
        for message in lines:
            connection.say(message)

@command
@mod_only
@short('Creates a value')
@long('''!add list [name]
        Creates a list with the given name
        !add dict [name]
        Creates a dictionary with the given name
        !add [list-name] [value]
        Adds the given value to a list
        !add [dict-name] [key] [value]
        Assigns the given value to the key in the dictionary''')
def add(connection, event, body):
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
@mod_only
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

