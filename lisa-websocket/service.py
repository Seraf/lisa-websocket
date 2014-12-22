#!/usr/bin/env python

import tornado.ioloop
import tornado.web
from tornado.options import parse_command_line
import tornado.httpserver
from messages import PikaClient
from webserver import TornadoWebServer

import logging

LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
              '-35s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)


def main():
    parse_command_line()
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

    # Get a handle to the instance of IOLoop
    ioloop = tornado.ioloop.IOLoop.instance()

    application = TornadoWebServer()

    # Create the connection with rabbitmq
    pc = PikaClient()
    application.pika = pc

    # Start the HTTP Server
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(8080)

    # Start the IOLoop
    try:
        ioloop.start()
    except KeyboardInterrupt:
        ioloop.stop()

if __name__ == '__main__':
    main()
