import os
import pprint
import re
import shutil
import tempfile

import requests
import zmq

from util import zmqsockets


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
    def __init__(self, fetcher, url, chunk_size=10240, keep_file=False, keep_tempfile=False):
        self.fetcher = fetcher
        self.session = self.fetcher.session
        self.logger = self.fetcher.logger

        #self.receiver = DebuggingReceiver(self)
        self.receiver = BroadcastingReceiver(self)

        self.url = url
        self.chunk_size = chunk_size

        self.keep_file = keep_file
        self.keep_tempfile = keep_tempfile
        self.fd = None
        self.tempfile = None
        self.target_path = None

        self.response = None
        self.data_length = 0
        self.runnable = True

    def fetch(self):
        try:
            self.unsafe_fetch()
        except Exception as e:
            self.cleanup_tempfile()
            self.logger.exception(e)

    def unsafe_fetch(self):
        # allocate a tempfile
        self.allocate_tempfile()

        # fire pre-fetch callback
        self.receiver.pre_fetch()

        # establish connection and fetch headers, then fire callback
        self.response = self.session.get(self.url, prefetch=False)
        self.receiver.received_headers()

        # start receiving the body
        for data in self.response.iter_content(chunk_size=self.chunk_size):
            # update data cursor and store the chunk
            self.data_length += len(data)
            self.write_chunk(data)

            # fire received-data callback
            self.receiver.received_data(data)

            # are we shutting down?
            if not self.runnable:
                # clean up tempfile and fire receive-aborted callback
                self.cleanup_tempfile()
                self.receiver.receive_aborted()
                break

        # if we have not been aborted, move the data from a tempfile
        # to a target path
        if self.runnable:
            self.store_file()

    def allocate_tempfile(self):
        if self.keep_file or self.keep_tempfile:  # noop if option is disabled
            self.fd, self.tempfile = tempfile.mkstemp(suffix='.partial', prefix='fetch_')

    def cleanup_tempfile(self):
        if self.fd:
            os.close(self.fd)
        if not self.keep_tempfile:
            if self.tempfile and os.path.isfile(self.tempfile):
                os.unlink(self.tempfile)

    def write_chunk(self, data):
        if self.fd:  # noop if we have no file descriptor
            os.write(self.fd, data)

    def store_file(self):
        if self.keep_file:  # noop if option is disabled
            self.target_path = get_target_path(self.url)
            shutil.move(self.tempfile, self.target_path)
            self.cleanup_tempfile()

            # fire stored-file callback
            self.receiver.stored_file(self.target_path)

    # Convenience properties

    @property
    def content_length(self):
        try:
            return int(self.response.headers.get('content-length'))
        except (AttributeError, TypeError):
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


class DebuggingReceiver(object):
    def __init__(self, request):
        self.request = request
        self.logger = self.request.logger

    def pre_fetch(self):
        self.logger.debug('Fetching headers: %s' % self.request.url)

    def received_headers(self):
        dct = {
            'Status': self.request.status_code,
            'Content-Length': self.request.content_length,
            'Content-Type': self.request.content_type,
        }
        msg = 'Fetched headers: %s\n%s' % (self.request.url, pprint.pformat(dct))
        self.logger.debug(msg)

    def received_data(self, data):
        msg_progress = ''
        if self.request.content_length:
            msg_progress = ' of %s' % self.request.content_length

        msg_percent = ''
        if self.request.content_percent:
            msg_percent = ' %.1f%%' % self.request.content_percent

        msg = ('Received %s%s byte(s)%s: %s' %
               (self.request.data_length, msg_progress, msg_percent, self.request.url))

        self.logger.debug(msg)

    def receive_aborted(self):
        self.logger.debug('Aborted fetch: %s' % self.request.url)

    def stored_file(self, target_path):
        self.logger.debug('Stored file: %s: %s' % (target_path, self.request.url))


class BroadcastingReceiver(object):
    def __init__(self, request):
        self.request = request

        self.ctx = zmq.Context()
        self.socket = self.ctx.socket(zmq.PUB)
        self.socket.connect(zmqsockets.fetcher_broadcast)

    def get_state_dict(self):
        dct = {
            'action': None,
            'url': self.request.url,
            'status_code': self.request.status_code,
            'content_percent': self.request.content_percent,
        }
        return dct

    def pre_fetch(self):
        dct = self.get_state_dict()
        dct['action'] = 'starting'
        self.socket.send_pyobj(dct)

    def received_headers(self):
        pass

    def received_data(self, data):
        dct = self.get_state_dict()
        dct['action'] = 'received_data'
        self.socket.send_pyobj(dct)

    def receive_aborted(self):
        pass

    def stored_file(self, target_path):
        pass
