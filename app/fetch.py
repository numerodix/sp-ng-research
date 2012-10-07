import os
import pprint
import re
import shutil
import tempfile
import threading

import requests

import logutils
logger = logutils.getLogger('fetch')


shutdown_event = threading.Event()

def get_target_path(url):
    """Wget's algorithm"""
    target_path = os.path.basename(url) or 'index.html'
    while os.path.exists(target_path):
        try:
            root, seq = re.findall('^(.*)\.([0-9]+)$', target_path)[0]
            seq = int(seq)
        except IndexError:
            root = target_path
            seq = 0
        seq += 1
        target_path = '%s.%s' % (root, seq)
    return target_path

class Request(object):
    def __init__(self, fetcher, url, chunk_size=10240, keep_file=False):
        self.fetcher = fetcher
        self.session = self.fetcher.session
        self.url = url
        self.chunk_size = chunk_size

        self.keep_file = keep_file
        self.fd = None
        self.tempfile = None

        self.response = None
        self.data_length = 0
        self.runnable = True

    def fetch(self):
        try:
            self.unsafe_fetch()
        except:
            self.cleanup_tempfile()
            raise

    def unsafe_fetch(self):
        # allocate a tempfile
        self.allocate_tempfile()

        # fire pre-fetch callback
        self.fetcher.pre_fetch(self)

        # establish connection and fetch headers, then fire callback
        self.response = self.session.get(self.url, prefetch=False)
        self.fetcher.received_headers(self)

        # start receiving the body
        for data in self.response.iter_content(chunk_size=self.chunk_size):
            # update data cursor and store the chunk
            self.data_length += len(data)
            self.write_chunk(data)

            # fire received-data callback
            self.fetcher.received_data(self, data)

            # detect if the thread has been signalled to exit
            if shutdown_event.is_set():
                self.runnable = False

            # are we shutting down?
            if not self.runnable:
                # clean up tempfile and fire receive-aborted callback
                self.cleanup_tempfile()
                self.fetcher.receive_aborted(self)
                break

        # if we have not been aborted, move the data from a tempfile
        # to a target path
        if self.runnable:
            self.store_file()

    def allocate_tempfile(self):
        if self.keep_file:  # noop if option is disabled
            self.fd, self.tempfile = tempfile.mkstemp(suffix='.partial', prefix='fetch_')

    def cleanup_tempfile(self):
        if self.fd:
            os.close(self.fd)
        if self.tempfile and os.path.isfile(self.tempfile):
            os.unlink(self.tempfile)

    def write_chunk(self, data):
        if self.fd:  # noop if we have no file descriptor
            os.write(self.fd, data)

    def store_file(self):
        if self.keep_file:  # noop if option is disabled
            target_path = get_target_path(self.url)
            shutil.move(self.tempfile, target_path)
            self.cleanup_tempfile()

            # fire stored-file callback
            self.fetcher.stored_file(self, target_path)

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

    def __init__(self, keep_file=False):
        self.request_headers = {
            'User-Agent': self.user_agents[0]
        }
        self.session = requests.session(headers=self.request_headers)

    def fetch(self, urls, keep_file):
        self.fetch_threaded(urls, keep_file)

    def fetch_single(self, urls, keep_file):
        url = urls[0]
        request = Request(self, url, keep_file=keep_file)
        request.fetch()

    def fetch_threaded(self, urls, keep_file):
        threads = []
        for url in urls:
            request = Request(self, url, keep_file=keep_file)
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

    def stored_file(self, request, target_path):
        logger.debug('Stored file: %s: %s' % (target_path, request.url))


if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("", "--keep", action="store_true",
                      help="Store the download in a file")
    (options, args) = parser.parse_args()

    if not args:
        print("No urls given")

    f = Fetcher()
    f.fetch(args, keep_file=options.keep)
