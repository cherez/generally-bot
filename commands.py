commands = {}
aliases = {}
import db
from functools import wraps

from db import Dict, DictItem, List, ListItem, User


def command(func):
    name = func.__name__.replace('_', '-')
    commands[name] = func
    return func


def mod_only(func):
    @wraps(func)
    def restricted(connection, event, body):
        nick = event.source.nick
        if not User.find(name=nick, mod=True):
            return "{} must be a mod to do that.".format(nick)
        return func(connection, event, body)

    if hasattr(restricted, 'long'):
        restricted.long = "MOD ONLY!\n" + restricted.long
    restricted.mod_only = True
    return restricted


def alias(*names):
    def wrapper(func):
        for name in names:
            aliases[name] = func
        return func

    return wrapper


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


@alias('commands')
@command
@short('Lists commands and usage')
@long('''!help
        Lists all available commands available to users with short descriptions
        !help [command ...]
        Gives detailed description of listed commands''')
def help(connection, event, body):
    if not body:
        choices = sorted(i[0] for i in commands.items() if not getattr(i[1], 'mod_only', False))
        connection.say("!" + ", !".join(choices))

        custom_commands = db.Dict.find(name='command').entries
        names = sorted(command.name for command in custom_commands)
        connection.say("Custom commands:")
        connection.say("!" + ", !".join(names))
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
    message = '!{:20s} -- {}'.format(name, doc)
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
    args = body.split(maxsplit=1)
    if len(args) < 2:
        return 'Usage: !add [type] [value]'
    target = args[0]
    body = args[1]
    if target in ['list', 'dict']:
        if len(body.split()) > 1:
            return 'Usage: !add {} [single word list name]'.format(target)
        if List.find(name=body):
            return "List {} already exists.".format(body)
        if Dict.find(name=body):
            return "Dict {} already exists.".format(body)
        type = List if target == 'list' else Dict
        row = type.Row()
        row.name = body
        db.db.save()
        return 'Added {} {}'.format(target, body)

    list = List.find(name=target)
    
    if list:
        db.find_or_make(ListItem, list=target, value=body)
        db.db.save()
        return 'Added ' + body + ' to ' + target

    dict = Dict.find(name=target)
    if dict:
        if len(body.split()) < 2:
            return 'Usage: !add " {} [key] [value]'.format(target)
        name, value = body.split(maxsplit=1)
        row = db.find_or_make(DictItem, dict=dict, name=name)
        row.value = value
        new = row._new
        db.db.save()
        if new:
            return 'Added ' + name + ' to ' + target
        else:
            return "{} updated to {}".format(name, value)
    return "I don't know what a " + target + " is."


@command
@mod_only
def remove(connection, event, body):
    '''Deletes a value.'''
    args = body.split(maxsplit=1)
    if len(args) < 2:
        return 'Usage: !remove [type] [value]'
    target = args[0]
    body = args[1]
    session = connection.db()
    if target == 'list':
        list = List.find(name=body)
        if not list:
            return "List {} does not exist.".format(body)
        for entry in list.entries:
            entry.destroy()
        list.destroy()
        db.db.save()
        return "Removed list {}.".format(target)

    if target == 'dict':
        dict = Dict.find(name=body)
        if not dict:
            return "Dict {} does not exist.".format(body)
        for entry in dict.entries:
            entry.destroy()
        dict.destroy()
        db.db.save()
        return "Removed dict {}.".format(target)

    list = List.find(name=target)
    dict = Dict.find(name=target)

    if list:
        item = ListItem.find(list=list, value=body)
        if not item:
            return "{} not in {}.".format(body, target)
        item.destroy()
        db.db.save()
        return "Removed {} from {}.".format(body, target)

    if dict:
        item = DictItem.find(dict=dict, name=body)
        if not item:
            return "{} not in {}.".format(body, target)
        item.destroy()
        db.db.save()
        return "Removed {} from {}.".format(body, target)

    if dicts:
        if not db.remove(session, db.DictItem, dict=target, name=body):
            return "{} not in {}.".format(body, target)
        return "Removed {} from {}.".format(body, target)
    return "I don't know what a " + target + " is."
