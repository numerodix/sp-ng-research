#!/usr/bin/env python

import time
import threading
from threading import Thread

import zmq


url_worker = "inproc://fetch_queue"
url_control = "inproc://control"

def worker(ctx):
    fetch_queue = ctx.socket(zmq.PULL)
    fetch_queue.connect(url_worker)

    control = ctx.socket(zmq.DEALER)
    control.connect(url_control)

    t = threading.current_thread()
    ident = t.name

    control.send('ready')

    url = fetch_queue.recv()
    print 'cli: %s %s\n' % (t.name, url)

def main():
    ctx = zmq.Context()

    fetch_queue = ctx.socket(zmq.PUSH)
    fetch_queue.bind(url_worker)

    control = ctx.socket(zmq.ROUTER)
    control.bind(url_control)

    for i in xrange(2):
        t = Thread(target=worker, args=[ctx])
        t.start()

    while True:
        id_ = control.recv()
        signal = control.recv()
        print signal
        if signal == 'ready':
            break
        time.sleep(0.01)

    fetch_queue.send('http://stackoverflow.com/questions/6702187/python-zeromq-push-pull-lost-messages')
    fetch_queue.send('http://stackoverflow.com/questions/6702187/python-zeromq-push-pull-lost-messages')


if __name__ == '__main__':
    main()
