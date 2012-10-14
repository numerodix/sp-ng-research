import os
from os.path import abspath
from os.path import dirname
from os.path import exists
from os.path import join


class ZmqSockets(object):
    @property
    def fetcher_broadcast(self):
        basedir = self.get_basedir()
        fp = join(basedir, 'fetcher_broadcast')
        return 'ipc://%s' % fp

    def get_basedir(self):
        proj_base = dirname(abspath(__file__))
        basedir = join(proj_base, 'run')
        if not exists(basedir):
            os.makedirs(basedir)
        return basedir

zmqsockets = ZmqSockets()
