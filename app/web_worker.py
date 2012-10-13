import os
import re
import time
import urlparse

from werkzeug.wrappers import Request
from werkzeug.wrappers import Response

from app import db
from models import QueuedUrl
from models import Url

from workerbase import Worker


@Request.application
def webapp(request):
    return Response('Hi')

class WebWorker(Worker):
    def __init__(self):

        # call base, dispatches to .mainloop
        super(WebWorker, self).__init__()

    def mainloop(self):
        from werkzeug.serving import run_simple
        run_simple('localhost', 8000, webapp)
