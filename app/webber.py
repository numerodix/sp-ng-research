#!/usr/bin/env python

from multiprocessing import Queue
from multiprocessing import Process
import os
import signal
import time
import sys

from models import QueuedUrl

from db_worker import DbWorker
from fetch_worker import FetchWorker
from termgui_worker import TermguiWorker
from web_worker import WebWorker


class WebberDaemon(object):
    MODE_WEB = 0
    MODE_FETCH = 1

    def __init__(self, mode=MODE_WEB, seed_urls=None, num_fetchers=None):
        self.fetch_results = Queue()
        self.fetch_queue = Queue()

        self.mode = mode
        self.seed_urls = seed_urls
        self.num_fetchers = num_fetchers or 1

        self.child_procs = []


    def spawn_fetchers(self, count):
        for num in xrange(count):
            p = Process(target=FetchWorker, args=[
                self.fetch_queue,
                self.fetch_results,
            ])
            self.child_procs.append(p)
            p.start()

    def spawn_db_workers(self, count):
        for num in xrange(count):
            p = Process(target=DbWorker, args=[
                self.fetch_queue,
                self.fetch_results,
                self.seed_urls,
            ])
            self.child_procs.append(p)
            p.start()

    def spawn_termgui_workers(self, count):
        for num in xrange(count):
            p = Process(target=TermguiWorker)
            self.child_procs.append(p)
            p.start()

    def spawn_web_workers(self, count):
        for num in xrange(count):
            p = Process(target=WebWorker)
            self.child_procs.append(p)
            p.start()


    def init_fetch_mode(self):
        for url in self.seed_urls:
            qurl = QueuedUrl(url=url)
            self.fetch_queue.put(qurl)

        self.spawn_termgui_workers(1)
        self.spawn_fetchers(self.num_fetchers)

    def init_web_mode(self):
        self.spawn_db_workers(1)
        self.spawn_fetchers(self.num_fetchers)
        #self.spawn_web_workers(1)


    def mainloop(self):
        if self.mode == self.MODE_WEB:
            self.init_web_mode()
        elif self.mode == self.MODE_FETCH:
            self.init_fetch_mode()

        try:
            while True:
                time.sleep(0.1)

        except KeyboardInterrupt:
            for p in self.child_procs:
                try:
                    os.kill(p.pid, signal.SIGTERM)
                except OSError:
                    import traceback
                    traceback.print_exc()


if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("", "--fetchers", action="store", type="int",
                      help="Run with [x] workers")
    parser.add_option("", "--fetch", action="store_true",
                      help="Run in fetch mode")
    #parser.add_option("", "--keep", action="store_true",
    #                  help="Store the download in a file")
    (options, args) = parser.parse_args()

    if not args:
        print("No urls given")
        sys.exit(os.EX_USAGE)

    wd = WebberDaemon(
        seed_urls=args,
        num_fetchers=options.fetchers,
        mode=options.fetch and WebberDaemon.MODE_FETCH,
    )
    wd.mainloop()
