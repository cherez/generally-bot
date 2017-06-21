import sqlalchemy
from sqlalchemy import inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

from seaslug import *
import config


path = config.config['chan']

db = Database()

class User(db.Table):
    name = StrColumn(length=32)
    mod = BoolColumn()
    indices = [
        ['name']
    ]


class List(db.Table):
    name = StrColumn(length=64)
    entries = Belongs('ListItem', 'list')
    indices = [
        ['name']
    ]


class Dict(db.Table):
    name = StrColumn(length=64)
    entries = Belongs('DictItem', 'dict')
    indices = [
        ['name']
    ]


class ListItem(db.Table):
    list = ForeignColumn('List')
    value = StrBlobColumn()

    indices = [
        ['list', 'value']
    ]


class DictItem(db.Table):
    dict = ForeignColumn('Dict')
    name = StrColumn(length=64)
    value = StrBlobColumn()
    indices = [
        ['dict', 'name']
    ]


def init(path):
    db.connect(path)


def add(session, table, **values):
    try:
        session.add(table(**values))
        session.commit()
        return True
    except IntegrityError:
        session.rollback()
        return False


def find(session, table, **values):
    return session.query(table).filter_by(**values)


def find_or_make(table, **values):
    row = table.find(**values)
    if not row:
        row = table.Row()
        for key, value in values.items():
            setattr(row, key, value)
    return row


def remove(session, table, **values):
    try:
        count = session.query(table).filter_by(**values).delete()
        session.commit()
        return count
    except IntegrityError:
        session.rollback()
        return False


def new(obj):
    state = inspect(obj)
    return state.pending


def get(dict, name):
    dict = Dict.find(name=dict)
    item = DictItem.find(dict=dict, name=name)
    if not item:
        return None
    return item.value


def put(dict, name, value):
    dict = Dict.find(name=dict)
    item = find_or_make(DictItem, dict=dict, name=name)
    item.value = value
    db.save()


u = User
l = List
d = Dict
li = ListItem
di = DictItem