from sqlalchemy import (
    Column,
    Index,
    Integer,
    Unicode,
)

from .meta import Base
from passlib.apps import custom_app_context as pwd_context


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(Unicode)
    password = Column(Unicode)
    first_name = Column(Unicode)
    last_name = Column(Unicode)
    email = Column(Unicode)

    def __init__(self, **kwargs):
        self.username = kwargs['username']
        self.password = pwd_context.hash(kwargs['password'])
        self.first_name = kwargs['first_name']
        self.last_name = kwargs['last_name']
        self.email = kwargs['email']
