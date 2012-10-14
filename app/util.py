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


# ref: http://stackoverflow.com/questions/566746/how-to-get-console-window-width-in-python
def getTerminalSize():
    def ioctl_GWINSZ(fd):
        try:
            import fcntl, termios, struct, os
            cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
        except:
            return None
        return cr
    cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
    if not cr:
        try:
            fd = os.open(os.ctermid(), os.O_RDONLY)
            cr = ioctl_GWINSZ(fd)
            os.close(fd)
        except:
            pass
    if not cr:
        try:
            cr = (env['LINES'], env['COLUMNS'])
        except:
            cr = (25, 80)
    return int(cr[1]), int(cr[0])
