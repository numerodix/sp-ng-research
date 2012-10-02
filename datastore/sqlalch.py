#!/usr/bin/env python

import hashlib

from sqlalchemy import Column, Integer, String
from sqlalchemy import ForeignKey
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Url(Base):
    __tablename__ = 'urls'

    id = Column(Integer, primary_key=True)
    url = Column(String)
    hash = Column(String)
    level = Column(Integer)

    parent_id = Column(Integer, ForeignKey('urls.id'))
    children = relationship(
        'Url',
        backref=backref('parent', remote_side=[id])
    )

    def __init__(self, url, level, children=None):
        self.url = url
        self.hash = hashlib.md5(url).hexdigest()
        self.level = level
        self.children = children or []

    def __repr__(self):
        return ("<Url(level %s, %s children, '%s')>" %
                (self.level, len(self.children), self.url))


def main():
    engine = create_engine('sqlite:///:memory:')
    #engine = create_engine('sqlite:///store.sqlite')
    Session = sessionmaker(bind=engine)
    session = Session()

    Base.metadata.create_all(engine)

    demoset = {
        'http://larrythecow.org/universe/':
        [
            'http://steveno.wordpress.com/2012/10/01/capture-2/',
            'http://blog.siphos.be/2012/09/git-patch-apply/',
        ],
        'http://planetkde.org/':
        [
            'http://www.sinny.in/node/24',
            'http://freininghaus.wordpress.com/2012/10/02/dolphin-bug-fixes-in-kde-4-9-2/',
        ],
    }

    for parent, children in demoset.items():
        ch = [Url(c, 2) for c in children]
        url = Url(parent, 1, children=ch)
        session.add(url)

    session.commit()

    for url in session.query(Url).filter(Url.level == 1):
        print url
        for i, ch in enumerate(url.children, 1):
            print ' ', i, ch


if __name__ == '__main__':
    main()
