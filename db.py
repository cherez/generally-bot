import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.exc import IntegrityError

Base = declarative_base()


class User(Base):
    __tablename__ = 'USERS'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
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

def remove(session, table, **values):
    try:
        session.query(table).filter_by(**values).delete()
        session.commit()
        return True
    except IntegrityError:
        session.rollback()
        return False
