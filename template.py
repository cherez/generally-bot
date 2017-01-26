import db
import re
import random

dict_pattern = re.compile('\{[^\}\s]*\}')
list_pattern = re.compile('\[[^\]\s]*\]')

def render(session, template, scope='global'):
    patterns = dict_pattern.findall(template)
    for match in patterns:
        dict = match[1:-1]
        if ':' in dict:
            dict, name = dict.split(':', maxsplit = 1)
        else:
            dict, name = scope, dict
        value = db.get(session, dict, name) or ''
        template = template.replace(match, value)


    patterns = list_pattern.findall(template)
    for match in patterns:
        list = match[1:-1]
        items = db.find(session, db.ListItem, list=list).all()
        if items:
            template = template.replace(match, random.choice(items).value, 1)
    return template
