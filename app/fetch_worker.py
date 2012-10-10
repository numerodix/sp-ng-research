import time

from request import Fetcher
from workerbase import Worker


class FetchWorker(Worker):
    def __init__(self, fetch_queue, fetch_results):
        self.fetch_queue = fetch_queue
        self.fetch_results = fetch_results

        super(FetchWorker, self).__init__()

    def run(self):
        while True:
            url = self.fetch_queue.get()
            if url:
                self.logger.debug("Got from queue: %s" % url)
                fetcher = Fetcher()
                fetcher.fetch(url)
            time.sleep(1)
