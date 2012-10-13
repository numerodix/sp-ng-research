import time
import sys

import zmq

import ansi

from workerbase import Worker


class TermguiWorker(Worker):
    def __init__(self):
        self.ctx = zmq.Context()
        self.socket = self.ctx.socket(zmq.SUB)
        self.socket.bind('ipc://events')
        self.socket.setsockopt(zmq.SUBSCRIBE, '')

        self.gui = ProgressbarTable()

        super(TermguiWorker, self).__init__()

    def render(self, msg):
        action = msg.get('action')
        url = msg.get('url')
        perc = float(msg.get('content_percent') or 0)

        self.gui.update(url, perc)

    def mainloop(self):
        while True:
            msg = self.socket.recv_pyobj()
            #print msg
            self.render(msg)


class ProgressbarTable(object):
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
        gui.update(key, perc)
        time.sleep(.15)
