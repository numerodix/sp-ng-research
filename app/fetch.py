import pprint
import threading

import requests

import logutils
logger = logutils.getLogger('fetch')


shutdown_event = threading.Event()

class Request(object):
    def __init__(self, fetcher, url, chunk_size=10240):
        self.fetcher = fetcher
        self.session = self.fetcher.session
        self.url = url
        self.chunk_size = chunk_size

        self.response = None
        self.data_length = 0
        self.runnable = True

    def fetch(self):
        self.fetcher.pre_fetch(self)

        self.response = self.session.get(self.url, prefetch=False)
        self.fetcher.received_headers(self)

        for data in self.response.iter_content(chunk_size=self.chunk_size):
            self.data_length += len(data)
            self.fetcher.received_data(self, data)

            if shutdown_event.is_set():
                self.runnable = False

            if not self.runnable:
                self.fetcher.receive_aborted(self)
                break

    @property
    def content_length(self):
        try:
            return int(self.response.headers.get('content-length'))
        except (AttributeError, ValueError):
            pass

    @property
    def content_percent(self):
        if self.content_length:
            return float(100 * self.data_length) / self.content_length

    @property
    def content_type(self):
        if not self.response is None:
            return self.response.headers.get('content-type')

    @property
    def status_code(self):
        if not self.response is None:
            return self.response.status_code


class Fetcher(object):
    user_agents = [
        # chrome/win7
        'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.66 Safari/535.11',
        # firefox/win7
        'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0a2) Gecko/20110613 Firefox/6.0a2',
        # ie10/win7
        'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)',
    ]

    def __init__(self):
        self.request_headers = {
            'User-Agent': self.user_agents[0]
        }
        self.session = requests.session(headers=self.request_headers)

    def fetch(self, urls):
        self.fetch_threaded(urls)

    def fetch_single(self, urls):
        url = urls[0]
        request = Request(self, url)
        request.fetch()

    def fetch_threaded(self, urls):
        threads = []
        for url in urls:
            request = Request(self, url)
            t = threading.Thread(target=request.fetch)
            threads.append(t)
            t.start()

        alive = threads[:]
        try:
            while alive:
                for t in alive:
                    if t.is_alive():
                        t.join(timeout=0.1)
                    else:
                        alive.remove(t)
        except (KeyboardInterrupt, SystemExit):
            shutdown_event.set()

    # Callbacks

    def pre_fetch(self, request):
        logger.debug('Fetching headers: %s' % request.url)

    def received_headers(self, request):
        dct = {
            'Status': request.status_code,
            'Content-Length': request.content_length,
            'Content-Type': request.content_type,
        }
        msg = 'Fetched headers: %s\n%s' % (request.url, pprint.pformat(dct))
        logger.debug(msg)

    def received_data(self, request, data):
        msg_progress = ''
        if request.content_length:
            msg_progress = ' of %s' % request.content_length

        msg_percent = ''
        if request.content_percent:
            msg_percent = ' %.1f%%' % request.content_percent

        msg = ('Received %s%s byte(s)%s: %s' %
               (request.data_length, msg_progress, msg_percent, request.url))

        logger.debug(msg)

    def receive_aborted(self, request):
        logger.debug('Aborted fetch: %s' % request.url)


if __name__ == '__main__':
    import sys
    f = Fetcher()
    f.fetch(sys.argv[1:])
