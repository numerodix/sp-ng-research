#!/usr/bin/env python

import sys

from twisted.web import server
from twisted.web import resource
from twisted.internet import reactor
from twisted.python import log

from jinja2 import Environment
from jinja2 import FileSystemLoader


class IndexResource(resource.Resource):
    isLeaf = True
    numberRequests = 0

    def render_GET(self, request):
        self.numberRequests += 1
        msg = "I am request #%s\n" % self.numberRequests

        import os
        d = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
        loader = FileSystemLoader(d)
        env = Environment(loader=loader)
        temp = env.get_template('index.html')
        html = temp.render(msg=msg)
        print html

        request.setHeader('content-type', 'text/html')
        return html.encode('utf8')

reactor.listenTCP(8000, server.Site(IndexResource()))
log.startLogging(sys.stdout)
reactor.run()
