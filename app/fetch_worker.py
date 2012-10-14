import time

import requests

from models import Resource

from request import Request
from workerbase import Worker


class FetchWorker(Worker):
    user_agents = [
        # chrome/win7
        'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.66 Safari/535.11',
        # firefox/win7
        'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0a2) Gecko/20110613 Firefox/6.0a2',
        # ie10/win7
        'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)',
    ]

    def __init__(self, fetch_queue, fetch_results):
        # init multiproc data structures
        self.fetch_queue = fetch_queue
        self.fetch_results = fetch_results

        # init myself
        self.request_headers = {
            'User-Agent': self.user_agents[0],
            'Accept-Encoding': None,  # disable gzip
        }
        self.session = requests.session(headers=self.request_headers)

        # call base, dispatches to .mainloop
        super(FetchWorker, self).__init__()

    def fetch(self, qres):
        request = Request(self, qres.url, keep_tempfile=True)
        request.fetch()

        res = Resource(
            url=qres.url,
            level=qres.level,
            context=qres.context,
            status_code=request.status_code,
            content_type=request.content_type,
            content_length=request.content_length,
        )
        msg = {
            'qres': qres,
            'res': res,
            'filepath': request.tempfile,
        }
        self.fetch_results.put(msg)

    def mainloop(self):
        while True:
            qres = self.fetch_queue.get()
            if qres:
                self.logger.debug("Got from queue: %s" % qres)
                self.fetch(qres)
            else:
                time.sleep(0.01)
