#!/usr/bin/env python

import sys

from twisted.web import server
from twisted.web import resource
from twisted.internet import reactor
from twisted.python import log


class IndexResource(resource.Resource):
    isLeaf = True
    numberRequests = 0

    def render_GET(self, request):
        self.numberRequests += 1
        request.setHeader('content-type', 'text/plain')
        return "I am request #%s\n" % self.numberRequests

reactor.listenTCP(8000, server.Site(IndexResource()))
log.startLogging(sys.stdout)
reactor.run()
