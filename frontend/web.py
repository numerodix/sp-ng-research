#!/usr/bin/env python

import os
import sys

from twisted.web import server
from twisted.web import static
from twisted.web import resource
from twisted.internet import reactor
from twisted.python import log

from jinja2 import Environment
from jinja2 import FileSystemLoader


def get_package_path():
    return os.path.dirname(os.path.abspath(__file__))

class Root(resource.Resource):
    hits = 0

    def __init__(self):
        resource.Resource.__init__(self)
        self.putChild('', Home(self))

    def getChild(self, name, request):
        self.hits += 1
        if request.uri.startswith('/static/'):
            fp = os.path.join(get_package_path(), 'static')
            return static.File(fp)
        return resource.ErrorPage(404, '404', 'Not found')

class Home(resource.Resource):
    pageviews = 0

    def __init__(self, root):
        self.root = root

    def render_GET(self, request):
        self.pageviews += 1
        self.root.hits += 1
        msg = "Page views: %s, Hits: %s\n" % (self.pageviews, self.root.hits)

        path = os.path.join(get_package_path(), 'templates')
        loader = FileSystemLoader(path)
        env = Environment(loader=loader)
        temp = env.get_template('index.html')
        html = temp.render(
            title="Webber",
            msg=msg
        )

        request.setHeader('content-type', 'text/html')
        return html.encode('utf8')


reactor.listenTCP(8000, server.Site(Root()))
log.startLogging(sys.stdout)
reactor.run()
