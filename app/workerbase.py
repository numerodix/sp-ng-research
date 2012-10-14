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

        self.child_procs = []

        self.mainloop()

    def signal_hander(self, signum, frame):
        self.logger.info("Got signal: %s, shutting down" % signum)

        for p in self.child_procs:
            try:
                os.kill(p.pid, signal.SIGTERM)
            except OSError:
                import traceback
                traceback.print_exc()

        sys.exit()

    def mainloop(self):
        raise NotImplementedError
