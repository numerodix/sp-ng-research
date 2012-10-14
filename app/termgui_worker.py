import re
import time
import sys

import zmq

import ansi

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

    def render(self, msg):
        self.gui.update(msg)

    def mainloop(self):
        while True:
            msg = self.socket.recv_pyobj()
            #print msg
            self.render(msg)


class _ProgressbarTable(object):
    def __init__(self):
        self.linekeys = []

    def update(self, linekey, perc):
        key_width = 36
        padding = 1
        bar_width = 32
        perc_width = 1 + 5

        ln = int(bar_width * (float(perc) / 100))
        fill_ln = bar_width - ln - 1

        pr = '=' * ln
        fill = ' ' * fill_ln

        cont_ln = 2
        fix_ln = (key_width / 2) - cont_ln
        prefix = linekey[:fix_ln]
        suffix = linekey[-fix_ln + cont_ln:]
        cont = '.' * cont_ln
        key = '%s%s%s' % (prefix, cont, suffix)

        msg = '%s [%s>%s] %2.1f%%\r' % (key, pr, fill, perc)
        self.render_line(linekey, msg)

    def render_line(self, linekey, line):
        if linekey not in self.linekeys:
            self.linekeys.append(linekey)
            ansi.write('\n')  # add a row to our table

        idx = self.linekeys.index(linekey)
        y = len(self.linekeys) - idx

        ansi.up(y)
        ansi.clear_line()
        ansi.write(line)
        ansi.down(y)


def format_int(num):
    num = '%s' % num
    new = re.sub('(\d+)(\d{3})(,|$)', '\g<1>,\g<2>', num)
    if new != num:
        return format_int(new)
    return new

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

    def render_progressbar(self, percent):
        progbar_ln = self.term_width - 20
        progbar_struct_ln = 3
        progbar_prog_ln = progbar_ln - progbar_struct_ln
        done_ln = int( progbar_prog_ln * (float(percent) / 100))
        left_ln = progbar_prog_ln - done_ln
        done_s = '=' * done_ln + '>' if percent < 100 else '=' * (done_ln + 1)
        left_s = ' ' * left_ln
        return '[{0}{1}]'.format(done_s, left_s)

    def render(self, msg):
        action = msg.get('action') or ''
        url = msg.get('url')
        status_code = msg.get('status_code')
        content_length = msg.get('content_length') or '?'
        content_percent = int(msg.get('content_percent') or 0)
        content_type = msg.get('content_type')

        # render rows
        row1 = 'Fetching {0}'.format(url)

        row2 = '{0}'.format(action)
        if status_code:
            length_fmt = format_int(content_length)
            type_fmt = '[{0}]'.format(content_type) if content_type else ''
            row2 = 'HTTP {0}. Length: {1} {2}'.format(status_code, length_fmt, type_fmt)

        progress_bar = self.render_progressbar(content_percent)
        row3 = '{0:3d}% {1}'.format(content_percent, progress_bar)

        return url, [row1, row2, row3]

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
        self.set_term_width()
        self.display(msg)


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
            'content_percent': perc,
        })
        time.sleep(.15)
