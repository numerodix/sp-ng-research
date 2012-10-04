#!/usr/bin/env python

import os
import sys

from twisted.web import server
from twisted.web import resource
from twisted.internet import reactor
from twisted.python import log

from jinja2 import Environment
from jinja2 import FileSystemLoader

content_types = {
    '.png': 'image/png',
    '.css': 'text/css',
    '.js': 'application/x-javascript',
}


def get_package_path():
    return os.path.dirname(os.path.abspath(__file__))

class IndexResource(resource.Resource):
    isLeaf = True
    numberRequests = 0

    def render_GET(self, request):
        if request.uri.startswith('/static/'):
            return self.serve_static(request)

        self.numberRequests += 1
        msg = "I am request #%s\n" % self.numberRequests

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

    def serve_static(self, request):
        base_path = get_package_path()
        fp = os.path.join(base_path, request.uri[1:])
        if os.path.isfile(fp):
            _, ext = os.path.splitext(fp)
            content = open(fp).read()

            request.setHeader('content-type', content_types.get(ext))
            return content


reactor.listenTCP(8000, server.Site(IndexResource()))
log.startLogging(sys.stdout)
reactor.run()
