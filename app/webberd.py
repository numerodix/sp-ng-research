#!/usr/bin/env python

from multiprocessing import Queue
from multiprocessing import Process
import os
import signal
import time

from fetch_worker import FetchWorker


class WebberDaemon(object):
    def __init__(self):
        self.fetch_results = Queue()
        self.fetch_queue = Queue()

    def mainloop(self):
        procs = []
        for num in range(1):
            p = Process(target=FetchWorker, args=[
                self.fetch_queue,
                self.fetch_results,
            ])
            procs.append(p)
            p.start()

        try:
            while True:
                if self.fetch_queue.empty():
                    url = 'http://www.juventuz.net/'
                    self.fetch_queue.put(url)
                time.sleep(0.1)

        except KeyboardInterrupt:
            for p in procs:
                try:
                    os.kill(p.pid, signal.SIGTERM)
                except OSError:
                    import traceback
                    traceback.print_exc()


if __name__ == '__main__':
    wd = WebberDaemon()
    wd.mainloop()
