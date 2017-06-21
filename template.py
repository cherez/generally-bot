from db import List, ListItem, Dict, DictItem
import re
import random

dict_pattern = re.compile('\{[^\}\s]*\}')
list_pattern = re.compile('\[[^\]\s]*\]')


def render(template, scope='global'):
    patterns = dict_pattern.findall(template)
    for match in patterns:
        dict = match[1:-1]  # strip the { }
        if ':' in dict:
            dict, name = dict.split(':', maxsplit=1)
        else:
            dict, name = scope, dict
        dict = Dict.find(name=dict)
        item = DictItem.find(dict=dict, name=name)
        template = template.replace(match, item.value)

    patterns = list_pattern.findall(template)
    for match in patterns:
        list = match[1:-1]  # strip the [ ]
        items = [i for i in List.find(List.name == list).entries]
        if items:
            template = template.replace(match, random.choice(items).value, 1)
    return template
