import re
import time
import sys

import zmq

from lib import ansi

from stringformat import format_eta
from stringformat import format_int
from stringformat import format_rate
from util import getTerminalSize
from util import zmqsockets
from workerbase import Worker


class TermguiWorker(Worker):
    def __init__(self):
        self.ctx = zmq.Context()
        self.socket = self.ctx.socket(zmq.SUB)
        self.socket.bind(zmqsockets.fetcher_broadcast)
        self.socket.setsockopt(zmq.SUBSCRIBE, '')

        self.gui = ProgressbarTable()

        super(TermguiWorker, self).__init__()

    def mainloop(self):
        while True:
            msg = self.socket.recv_pyobj()
            self.gui.update(msg)


class ProgressbarTable(object):
    """ A table made up of multi-row cells.

    Example with 3 rows per cell:
row1  Fetching http://ubuntuarchive.xfree.com.ar/ubuntu/ls-lR.gz
      HTTP 200. Length: 12,322,257 [application/x-gzip]
      5% [====>                            ] 705,290      198K/s  eta 70s     ^
row0  Fetching http://debian.com/readme.html
      Connecting...
      0% [                                 ] 705,290      198K/s  eta 70s     ^

    Basic principle: All movement uses relative coordinates. And each movement
    operation should leave the cursor in the bottom right hand corner of the cell.
    """
    def __init__(self):
        self.cell_keys = []
        self.cell_height = 3

        self.update_interval = 0.1
        self.last_update = 0

        self.term_width = None
        self.set_term_width()

    def set_term_width(self):
        if not self.term_width:
            w, _ = getTerminalSize()
            self.term_width = w

    def get_cell_index(self, key):
        return self.cell_keys.index(key)

    def add_cell(self, key):
        if not key in self.cell_keys:
            self.cell_keys.insert(0, key)

            y = self.cell_height
            # if this is the first key
            if len(self.cell_keys) == 1:
                y = self.cell_height - 1

            ansi.write('\n' * y)
            ansi.move_horizontal(self.term_width)

    def move_to(self, from_key, to_key):
        idx_from = self.get_cell_index(from_key)
        idx_to = self.get_cell_index(to_key)

        y = (idx_from - idx_to) * self.cell_height

        if y > 0:
            ansi.down(y)
        elif y < 0:
            ansi.up(-y)
        ansi.move_horizontal(self.term_width)

    def move_from_the_bottom_to(self, to_key):
        return self.move_to(self.cell_keys[0], to_key)

    def move_to_the_bottom_from(self, from_key):
        return self.move_to(from_key, self.cell_keys[0])

    def display(self, msg):
        key, rows = self.render(msg)

        # add a row to our table
        self.add_cell(key)

        # display rows
        self.move_from_the_bottom_to(key)
        ansi.up(2)
        for i, row in enumerate(rows):
            ansi.move_horizontal(0)
            if i > 0:
                ansi.down(1)
            ansi.clear_line()
            ansi.write(row)
            ansi.move_horizontal(self.term_width)
        self.move_to_the_bottom_from(key)

    def update(self, msg):
        action = msg.get('action')
        if (action == 'Receiving body' and
            time.time() - self.last_update > self.update_interval):
            self.last_update = time.time()
            self.set_term_width()
            self.display(msg)


    def render_progressbar(self, percent, width):
        progbar_struct_ln = 3
        progbar_prog_ln = width - progbar_struct_ln

        done_ln = int( progbar_prog_ln * (float(percent) / 100))
        left_ln = progbar_prog_ln - done_ln

        done_s = '=' * done_ln + '>' if percent < 100 else '=' * (done_ln + 1)
        left_s = ' ' * left_ln

        return '[{0}{1}]'.format(done_s, left_s)

    def render(self, msg):
        action = msg.get('action') or ''
        url = msg.get('url')
        content_length = msg.get('content_length') or '?'
        content_received_length = msg.get('content_received_length') or '?'
        content_received_percent = int(msg.get('content_received_percent') or 0)
        content_type = msg.get('content_type')
        eta = int(msg.get('eta') or 0)
        rate = int(msg.get('rate') or 0)
        status_code = msg.get('status_code')

        # render rows
        row1 = 'Fetching {0}'.format(url)

        row2 = '{0}'.format(action)
        if status_code:
            length_fmt = format_int(content_length)
            type_fmt = '[{0}]'.format(content_type) if content_type else ''
            row2 = 'HTTP {0}. Length: {1} {2}'.format(status_code, length_fmt, type_fmt)

        progress_bar = self.render_progressbar(content_received_percent, self.term_width - 40)
        recv_fmt = format_int(content_received_length)
        rate_fmt = format_rate(rate)
        eta_fmt = ''
        if content_received_percent < 100:
            eta_fmt = 'eta {0}'.format(format_eta(eta))
        row3 = '{0:3d}% {1} {2:12} {3:>6}  {4}'.format(
            content_received_percent, progress_bar, recv_fmt, rate_fmt, eta_fmt,
        )

        return url, [row1, row2, row3]


if __name__ == '__main__':
    import random
    gui = ProgressbarTable()

    keys = ['a', 'b', 'c', 'd', 'e']
    keys = [
        'http://ubuntu.daupheus.com/quantal/ubuntu-12.10-beta2-desktop-i386.iso',
        'http://ubuntu.daupheus.com/quantal/ubuntu-12.10-beta2-desktop-armhf+omap4.img',
    ]
    for perc in xrange(100):
        key = random.choice(keys)
        gui.update({
            'url': key,
            'status_code': 200,
            'content_received_percent': perc,
        })
        time.sleep(.15)
