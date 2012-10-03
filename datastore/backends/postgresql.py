from twisted.internet import reactor
from twisted.python import log, util

from txpostgres import txpostgres

from model.model import UrlModel


class DbManager(object):
    def initialize(self):
        d = self.restoreConnection(None)
        d.addCallback(lambda _: self.conn.cursor())
        return d.addCallback(lambda c: c.execute(self.schema))

    def create_schema(self):
        d = self.restoreConnection(None)
        d.addCallback(lambda _: self.conn.cursor())
        return d.addCallback(lambda c: c.execute(self.schema))

    def drop_schema(self):
        c = self.conn.cursor()
        d = c.execute("drop table %s" % self.table_name)
        return d.addCallback(lambda _: self.conn.close())

    def restoreConnection(self, res):
        """
        Restore the connection to the database and return whatever argument has
        been passed through. Useful as an addBoth handler for tests that
        disconnect from the database.
        """
        self.conn = txpostgres.Connection()
        d = self.conn.connect(database='webber')
        d.addErrback(log.err)
        return d.addCallback(lambda _: res)

manager = DbManager()


class Url(UrlModel, DbManager):
    table_name = 'urls'
    schema = '''
    CREATE TABLE %s (
        id      integer PRIMARY KEY,
        url     varchar(255) NOT NULL,
        status  integer NOT NULL
    )
    ''' % table_name

    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.url = kwargs.get('url')
        self.status = kwargs.get('status')
        self.parent = kwargs.get('parent')
        self.children = kwargs.get('children')

    def get(self):
        c = self.conn.cursor()
        d = c.execute('select * from urls')
        d.addCallback(lambda _: c.fetchone())
        d.addCallback(lambda result: util.println('%s' % result))
        return d.addCallback(lambda _: c.close())

    def do(self):
        manager.d.addCallback(lambda _: manager.conn.runQuery(
            'select tablename from pg_tables'))
        manager.d.addCallback(lambda result: util.println(
            'All tables:', result))

        manager.d.addCallback(lambda _: manager.conn.close())
        manager.d.addErrback(lambda _: log.err)
        manager.d.addBoth(lambda _: reactor.stop())
    

if __name__ == '__main__':
    url = Url(
        id=1,
        url='http://twistedmatrix.com/trac/',
        status=200,
    )
    d = url.create_schema()
    d.addCallback(lambda _: url.get())
    #d.addCallback(lambda _: url.drop_schema())

    reactor.run()
