import os
import re
import time
import urlparse
from wsgiref.simple_server import make_server

from app import db

from workerbase import Worker


def webapp(environ, start_response):
    start_response('200 OK', [('Content-type', 'text/plain')])
    return 'Hi'

class WebWorker(Worker):
    def __init__(self):

        # call base, dispatches to .mainloop
        super(WebWorker, self).__init__()

    def mainloop(self):
        httpd = make_server('', 8000, webapp)
        httpd.handle_request()
