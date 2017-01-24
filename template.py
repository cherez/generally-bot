import db
import re
import random

pattern = re.compile('\[[^\]]*\]')

def render(session, template):
    patterns = pattern.findall(template)
    for match in patterns:
        list = match[1:-1]
        items = session.query(db.ListItem).filter(db.ListItem.list == list).all()
        if items:
            template = template.replace(match, random.choice(items).value, 1)
    return template
