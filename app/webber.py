#!/usr/bin/env python

from multiprocessing import Queue
from multiprocessing import Process
from multiprocessing.queues import Empty
import os
import signal
import time
import sys

from models import QueuedResource

from db_worker import DbWorker
from fetch_worker import FetchWorker
from termgui_worker import TermguiWorker
from web_worker import WebWorker


class WebberDaemon(object):
    MODE_WEB = 0
    MODE_FETCH = 1

    def __init__(self, mode=None, seed_urls=None, num_fetchers=None):
        self.fetch_results = Queue()
        self.fetch_queue = Queue()

        self.mode = mode or self.MODE_WEB
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
            ], kwargs=dict(
                fetch_queue_preload=self.num_fetchers * 2,
            ))
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


    def terminate_workers(self):
        for p in self.child_procs:
            try:
                os.kill(p.pid, signal.SIGTERM)
            except OSError:
                import traceback
                traceback.print_exc()


    def mainloop_fetch(self):
        completed_fetches = set()
        for url in self.seed_urls:
            qurl = QueuedResource(url=url)
            self.fetch_queue.put(qurl)

        self.spawn_termgui_workers(1)
        self.spawn_fetchers(self.num_fetchers)

        try:
            while True:
                msg = None
                try:
                    msg = self.fetch_results.get(True, 0.01)
                except Empty:
                    pass

                if msg:
                    url = msg.get('url')
                    completed_fetches.update([url.url])
                    if completed_fetches == set(self.seed_urls):
                        self.terminate_workers()
                        break
        except KeyboardInterrupt:
            self.terminate_workers()

    def mainloop_web(self):
        self.spawn_db_workers(1)
        self.spawn_termgui_workers(1)
        self.spawn_fetchers(self.num_fetchers)
        #self.spawn_web_workers(1)

        try:
            while True:
                time.sleep(0.03)
        except KeyboardInterrupt:
            self.terminate_workers()

    def mainloop(self):
        if self.mode == self.MODE_WEB:
            return self.mainloop_web()
        elif self.mode == self.MODE_FETCH:
            return self.mainloop_fetch()



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
