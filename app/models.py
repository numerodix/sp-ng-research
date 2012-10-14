from app import db


class QueuedResource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String, index=True)
    level = db.Column(db.Integer)
    context = db.Column(db.String)
    parent_url = db.Column(db.String)

    processing_status = db.Column(db.String, default='new')

    def __init__(self, **kwargs):
        if not 'level' in kwargs:
            kwargs['level'] = 0
        super(self.__class__, self).__init__(**kwargs)

    def __repr__(self):
        return "<{0}(level {1}, '{2}')>".format(
                self.__class__.__name__, self.level, self.url)

class Resource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String, index=True)
    level = db.Column(db.Integer)
    context = db.Column(db.String)

    status_code = db.Column(db.Integer)
    content_type = db.Column(db.String)
    content_length = db.Column(db.Integer)

    parent_id = db.Column(db.Integer, db.ForeignKey('resource.id'))
    children = db.relationship(
        'Resource',
        backref=db.backref('parent', remote_side=[id])
    )

    def __repr__(self):
        return "<{0}(level {1}, {2} children, '{3}')>".format(
                self.__class__.__name__, self.level, len(self.children), self.url)
