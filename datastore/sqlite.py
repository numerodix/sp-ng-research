#!/usr/bin/env python

import hashlib

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import sessionmaker


Base = declarative_base()

class Url(Base):
    __tablename__ = 'urls'

    id = Column(Integer, primary_key=True)
    hash = Column(String)
    url = Column(String)

    def __init__(self, url):
        self.url = url
        self.hash = hashlib.md5(url).hexdigest()

    def __repr__(self):
        return "<Url('%s', '%s')>" % (self.hash, self.url)


def main():
    #engine = create_engine('sqlite:///:memory:')
    engine = create_engine('sqlite:///store.sqlite')
    Session = sessionmaker(bind=engine)
    session = Session()

    Base.metadata.create_all(engine)

    url = Url('http://docs.sqlalchemy.org/en/rel_0_7/orm/tutorial.html')
    session.add(url)

    session.commit()

    print session.query(Url).count()


if __name__ == '__main__':
    main()
