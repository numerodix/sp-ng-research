from app import db


class QueuedUrl(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String, index=True)
    level = db.Column(db.Integer)
    context = db.Column(db.String)
    parent_url = db.Column(db.String)

    processing_status = db.Column(db.String, default='new')

    def __init__(self, **kwargs):
        if not 'level' in kwargs:
            kwargs['level'] = 0
        super(QueuedUrl, self).__init__(**kwargs)

    def __repr__(self):
        return ("<QueuedUrl(level %s, '%s')>" %
                (self.level, self.url))

class Url(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String, index=True)
    level = db.Column(db.Integer)
    context = db.Column(db.String)

    status_code = db.Column(db.Integer)
    content_type = db.Column(db.String)
    content_length = db.Column(db.Integer)

    parent_id = db.Column(db.Integer, db.ForeignKey('url.id'))
    children = db.relationship(
        'Url',
        backref=db.backref('parent', remote_side=[id])
    )

    def __repr__(self):
        return ("<Url(level %s, %s children, '%s')>" %
                (self.level, len(self.children), self.url))
