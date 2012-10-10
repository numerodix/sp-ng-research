#!/usr/bin/env python

from multiprocessing import Process
import os
import signal
import sys
import time
from wsgiref.util import setup_testing_defaults
from wsgiref.simple_server import make_server

from logutils import getLogger


def simple_app(environ, start_response):
    setup_testing_defaults(environ)

    status = '200 OK'
    headers = [('Content-type', 'text/plain')]

    start_response(status, headers)

    ret = ["%s: %s\n" % (key, value)
           for key, value in environ.iteritems()]
    return ret


class Worker(object):
    def __init__(self, port):
        self.port = port
        self.ident = "Worker:%s" % os.getpid()

        signal.signal(signal.SIGTERM, self.signal_hander)

        self.logger = getLogger(self.ident)
        self.logger.debug("Started")

        self.run()

    def signal_hander(self, signum, frame):
        self.logger.info("Got signal: %s, shutting down" % signum)
        self.httpd.socket.close()
        sys.exit()

    def run(self):
        self.httpd = make_server('', self.port, simple_app)
        print "serving at port", self.port
        self.httpd.serve_forever()


if __name__ == '__main__':
    port = int(sys.argv[1])

    procs = []
    for num in range(1):
        p = Process(target=Worker, args=[port])
        procs.append(p)
        p.start()

    try:
        while True:
            for p in procs:
                p.join(timeout=1)
    except KeyboardInterrupt:
        for p in procs:
            os.kill(p.pid, signal.SIGTERM)
