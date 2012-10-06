from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///store.sqlite'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost/crawl'
db = SQLAlchemy(app)


class QueuedUrl(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String, index=True)
    level = db.Column(db.Integer)
    context = db.Column(db.String)
    parent_url = db.Column(db.String)

    def __repr__(self):
        return ("<QueuedUrl(level %s, '%s')>" %
                (self.level, self.url))

class Url(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String, index=True)
    level = db.Column(db.Integer)
    context = db.Column(db.String)

    status_code = db.Column(db.Integer)

    parent_id = db.Column(db.Integer, db.ForeignKey('url.id'))
    children = db.relationship(
        'Url',
        backref=db.backref('parent', remote_side=[id])
    )

    def __repr__(self):
        return ("<Url(level %s, %s children, '%s')>" %
                (self.level, len(self.children), self.url))
