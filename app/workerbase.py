import os
import signal
import sys

from logutils import getLogger


class Worker(object):
    def __init__(self):
        self.ident = "%s-%s" % (self.__class__.__name__, os.getpid())

        signal.signal(signal.SIGTERM, self.signal_hander)

        self.logger = getLogger(self.ident)
        self.logger.debug("Started")

        self.run()

    def signal_hander(self, signum, frame):
        self.logger.warn("Got signal: %s, shutting down" % signum)
        sys.exit()

    def run(self):
        raise NotImplementedError


