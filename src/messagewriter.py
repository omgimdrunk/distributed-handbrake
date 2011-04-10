import client_0_8 as amqp

class MessageWriter(object):
    '''Creates and mantains a connection with a RabbitMQ server.
    
    Parameters are as follows:
    routing_key ***** Must be declared.  Gives both the routing key and queue name
    server='localhost'
    vhost='/'
    userid='guest'
    password='guest'
    exchange=''
    exchange_type='direct'
    exchange_durable=True
    exchange_auto_delete=False
    queue_durable=False
    queue_auto_delete=True
    
    Methods are:
    __init__: opens connection with server, establishes a channel, declares an exchange, declares a queue, and binds the queue to the exchange
    send_message: takes a string/pickled object and sends it to the queue
    close: closes the channel and connection'''
    
    def __init__(self, routing_key,  server='localhost', vhost='/', userid='guest', password='guest', exchange='', \
                  exchange_type='direct', exchange_durable=True, exchange_auto_delete=False, queue_durable=False, queue_auto_delete=True):
        '''Opens connection with server, establishes a channel, declares an exchange, declares a queue, and binds the queue to the exchange'''
        self._server=server
        self._vhost=vhost
        self._userid=userid
        self._password=password
        self._exchange=exchange
        self._routing_key=routing_key
        self._exchange_type=exchange_type
        self._exchange_durable=exchange_durable
        self._exchange_auto_delete=exchange_auto_delete
        self._queue_durable=queue_durable
        self._queue_auto_delete=queue_auto_delete
        
        self._connection = amqp.Connection(host=self._server, userid=self._userid, password=self._password, virtual_host=self._vhost)
        self._channel = self._connection.channel()
        self._channel.exchange_declare(exchange=self._exchange, type=self._exchange_type, durable=self._exchange_durable,  auto_delete=self._exchange_auto_delete)
        self._channel.queue_declare(queue=self._routing_key, durable=self._queue_durable,  auto_delete=self._queue_auto_delete)
        self._channel.queue_bind(queue=self._routing_key, exchange=self._exchange,  routing_key=self._routing_key)
        
    def send_message(self, message):
        '''Takes a string/pickled object and sends it to the queue'''
        msg=amqp.Message(message)
        self._channel.basic_publish(exchange=self._exchange, routing_key=self._routing_key, msg=msg)
        
    def close(self):
        '''Closes the channel and connection to the server'''
        self._channel.close()
        self._connection.close()
