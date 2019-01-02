import os
import sys

from sqlalchemy import Column, Integer, ForeignKey, String

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import relationship

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declared_attr


class Base(object):
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()


Base = declarative_base(cls=Base)


class User(Base):
    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    email = Column(String(80), nullable=False)
    picture = Column(String(250))


class Category(Base):
    __tablename__ = 'category'

    name = Column(String(80), nullable=False)
    cid = Column(Integer, primary_key=True)
    items = relationship("Items")
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        return {
                'category_name': self.name,
                'category_id': self.cid,
                'items': [i.serialize for i in self.items],
               }


class Items(Base):
    __tablename__ = 'items'

    name = Column(String(200), nullable=False)
    itemid = Column(Integer, primary_key=True)
    price = Column(String(8))
    description = Column(String(100))
    category_id = Column(Integer, ForeignKey('category.cid'))
    category = relationship(Category, back_populates='items')
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        return {
                'name': self.name,
                'itemid': self.itemid,
                'price': self.price,
                'description': self.description,
                'category_id': self.category_id,
               }


engine = create_engine('sqlite:///newcatalog.db')

Base.metadata.create_all(engine)
