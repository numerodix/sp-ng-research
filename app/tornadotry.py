#!/usr/bin/env python

from tornado import httpserver
from tornado import ioloop


def handle_request(request):
    import os
    print os.getpid()
    message = "You requested %s\n" % request.uri
    request.write("HTTP/1.1 200 OK\r\nContent-Length: %d\r\n\r\n%s" % (
        len(message), message))
    request.finish()


if __name__ == '__main__':
    #server = httpserver.HTTPServer(handle_request)
    #server.bind(8888)
    #server.start(0)  # Forks multiple sub-processes
    #ioloop.IOLoop.instance().start()



    http_server = httpserver.HTTPServer(handle_request)
    http_server.listen(8888)
    ioloop.IOLoop.instance().start()


