#!/usr/bin/env python

import hashlib

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///store.sqlite'
db = SQLAlchemy(app)


class Url(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String)
    hash = db.Column(db.String)
    level = db.Column(db.Integer)

    parent_id = db.Column(db.Integer, db.ForeignKey('url.id'))
    children = db.relationship(
        'Url',
        backref=db.backref('parent', remote_side=[id])
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
    db.create_all()

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
        db.session.add(url)

    db.session.commit()

    for url in db.session.query(Url).filter(Url.level == 1):
        print url
        for i, ch in enumerate(url.children, 1):
            print ' ', i, ch


if __name__ == '__main__':
    main()
