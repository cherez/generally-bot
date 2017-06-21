import db
from template import render
from db import Dict, DictItem


def find(connection, name):
    dict = Dict.find(name='command')
    item = DictItem.find(dict=dict, name=name)
    if not item:
        return None
    template = item.value

    def reader(connection, event, body):
        connection.say(render(template))

    return reader
