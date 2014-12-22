import tornado.ioloop
import tornado.web
import sockjs.tornado
import tornado.httpserver
from messages import PikaClient

import logging

LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
              '-35s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)


class WebSocketConnection(sockjs.tornado.SockJSConnection):
    """Websocket connection implementation"""
    # Class level variable
    clients = set()

    def on_open(self, info):
        # Add client to the clients list
        #Initialize new pika client object for this websocket.
        self.pika_client = PikaClient()
        self.pika_client.on_exchange_declared()

        #Assign websocket object to a Pika client object attribute.
        self.pika_client.websocket = self

        self.clients.add(self)

    def on_message(self, message):
        LOGGER.info('Message from websocket : %s', message)
        #Publish the received message on the RabbitMQ
        self.pika_client.message_server(message)

    def on_close(self):
        # Remove client from the clients list
        self.pika_client.on_basic_cancel()
        self.clients.remove(self)


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('frontend/index.html')


class TornadoWebServer(tornado.web.Application):
    def __init__(self):
        WebSocketRouter = sockjs.tornado.SockJSRouter(WebSocketConnection, '/websocket')

        handlers = WebSocketRouter.urls + [
            ('/', MainHandler),
            ('/(.*)', tornado.web.StaticFileHandler, {'path': 'frontend'})
        ]

        settings = dict()
        tornado.web.Application.__init__(self, handlers, **settings)
