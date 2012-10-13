import time
import sys

import zmq

from workerbase import Worker


def write(s):
    sys.stdout.write(s)
    sys.stdout.flush()

class TermguiWorker(Worker):
    def __init__(self):
        self.ctx = zmq.Context()
        self.socket = self.ctx.socket(zmq.SUB)
        self.socket.connect('ipc://events')
        self.socket.setsockopt(zmq.SUBSCRIBE, '')

        super(TermguiWorker, self).__init__()

    def render(self, msg):
        action = msg.get('action')
        url = msg.get('url')
        perc = int(msg.get('content_percent') or 0)

        if action == 'received_data':
            write('.')

    def mainloop(self):
        while True:
            msg = self.socket.recv_pyobj()
            self.render(msg)
