import sqlalchemy
from sqlalchemy import inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

Base = declarative_base()


class User(Base):
    __tablename__ = 'USERS'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String, index=True, nullable=False)
    mod = sqlalchemy.Column(sqlalchemy.Boolean, nullable=False)

class List(Base):
    __tablename__ = 'LISTS'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String, unique=True, nullable=False)

class Dict(Base):
    __tablename__ = 'DICTS'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String, unique=True, nullable=False)

class ListItem(Base):
    __tablename__ = 'LIST_ITEMS'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    list = sqlalchemy.Column(sqlalchemy.String, index=True, nullable=False)
    value = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    __table_args__ = (UniqueConstraint('list', 'value', name='_list_value_uc'),)

class DictItem(Base):
    __tablename__ = 'DICT_ITEMS'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    dict = sqlalchemy.Column(sqlalchemy.String, index=True, nullable=False)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    value = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    __table_args__ = (UniqueConstraint('dict', 'name', name='_dict_name_uc'),)


def init(path):
    engine = sqlalchemy.create_engine('sqlite:///{}.sqlite'.format(path), connect_args={'check_same_thread':False})
    session_factory = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return session_factory

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

def find_or_make(session, table, **values):
    try:
        return find(session, table, **values).one()
    except NoResultFound:
        result = table(**values)
        session.add(result)
        return result

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

def get(session, dict, name):
    items = find(session, DictItem, dict=dict, name=name).all()
    if not items:
        return None
    return items[0].value


def put(session, dict, name, value):
    item = find_or_make(session, DictItem, dict=dict, name=name)
    item.value = value
    session.commit()
