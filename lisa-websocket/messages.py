from pika.adapters.tornado_connection import TornadoConnection
import pika

import logging


LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
              '-35s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)


class PikaBaseConnection(object):
    """
        Base class for pika connection. We use one object of this to handle all channels.
        We using One connection and one Channel througout this tornado IOLoop. and the excahnges
        were defined here too, we can modify according to our requirement.
    """

    def __init__(self):
        'Initialize the connection with RabbitMQ server.'
        self.connecting = False
        self.connected = False
        self.connection = None
        self.channel = None

    def connect(self):

        if self.connecting:
            LOGGER.info('PikaClient: Already connecting to RabbitMQ')
            return

        LOGGER.info('PikaClient: Connecting to RabbitMQ on localhost:5672, Object: %s' % (self,))

        self.connecting = True

        credentials = pika.PlainCredentials('guest', 'guest')
        param = pika.ConnectionParameters(host='localhost',
                                          port=5672,
                                          virtual_host="/",
                                          credentials=credentials)
        self.connection = TornadoConnection(param,
                                            on_open_callback=self.on_connected)

    def on_connected(self, connection):

        LOGGER.info('PikaClient: [Using common Connection] localhost:5672')

        self.connected = True
        self.connection = connection

        self.connection.channel(self.on_channel_open)

    def on_channel_open(self, channel):
        LOGGER.info('PikaClient: Channel Open, Declaring Exchange, Channel ID: %s' % (channel,))
        self.channel = channel

        self.channel.exchange_declare(exchange='lisa',
                                      type="topic")


class PikaBaseConnectionSingleton(object):
    """
    Singleton version of the message class.

    Being a singleton, this class should not be initialised explicitly
    and the ``get`` classmethod must be called instead.

    To call one of this class's methods you have to use the ``get``
    method in the following way:
    ``LisaMessages.get().themethodname(theargs)``
    """

    __instance = None

    def __init__(self):
        """
        Initialisation: this class should not be initialised
        explicitly and the ``get`` classmethod must be called instead.
        """

        if self.__instance is not None:
            raise Exception("Singleton can't be created twice !")

    def get(self):
        """
        Actually create an instance
        """
        if self.__instance is None:
            self.__instance = PikaBaseConnection()
            LOGGER.info("PikaBaseConnectionSingleton initialised")
        return self.__instance
    get = classmethod(get)


class PikaClient(object):

    def __init__(self):
        # Construct a queue name we'll use for this instance only

        self.rabbit_conn = PikaBaseConnectionSingleton.get()
        if not self.rabbit_conn.connection:
            self.rabbit_conn.connect()

        #Giving unique queue for each consumer under a channel.
        self.queue_name = "websocket-%s" % (id(self),)

        self.websocket = None
        self.ctag = None

    def on_exchange_declared(self):
        LOGGER.info('PikaClient: Exchange Declared, Declaring Queue')
        self.rabbit_conn.channel.queue_declare(auto_delete=True,
                                   queue=self.queue_name,
                                   exclusive=True,
                                   callback=self.on_queue_declared)

    def on_queue_declared(self, frame):
        LOGGER.info('PikaClient: Queue Declared, Binding Queue')
        self.rabbit_conn.channel.queue_bind(exchange='lisa',
                                queue=self.queue_name,
                                routing_key="client.websocket.%s" % id(self),
                                callback=self.on_queue_bound)
        self.rabbit_conn.channel.queue_bind(exchange='lisa',
                                queue=self.queue_name,
                                routing_key="client.websocket.all",
                                callback=self.on_queue_bound)

        self.rabbit_conn.channel.queue_bind(exchange='lisa',
                                queue=self.queue_name,
                                routing_key="client.all",
                                callback=self.on_queue_bound)

    def on_queue_bound(self, frame):
        LOGGER.info('PikaClient: Queue Bound, Issuing Basic Consume')
        self.ctag = self.rabbit_conn.channel.basic_consume(consumer_callback=self.on_pika_message,
                                               queue=self.queue_name,
                                               no_ack=True)

    def on_pika_message(self, channel, method, header, body):
        LOGGER.info('PikaCient: Message receive, delivery tag #%i' % method.delivery_tag)

        #Send the Consumed message via Websocket to browser.
        self.websocket.send(body)
        #self.rabbit_conn.channel.basic_ack(delivery_tag=method.delivery_tag)

    def on_basic_cancel(self):
        'Only close the Consumer queue, so no problem with channel'

        LOGGER.info('PikaClient: Basic Cancel Ok')

        #Close the consumer/queue associated with this websocket client or browser.
        self.rabbit_conn.channel.queue_delete(queue=self.queue_name)

    #def on_closed(self, connection):
        # We've closed our pika connection so stop the demo
    #    tornado.ioloop.IOLoop.instance().stop()

    def message_server(self, ws_msg):
        #Publish the message from Websocket to RabbitMQ
        properties = pika.BasicProperties(content_type="text/plain", delivery_mode=1)

        self.rabbit_conn.channel.basic_publish(exchange='lisa',
                                   routing_key='server',
                                   body=ws_msg,
                                   properties=properties)

