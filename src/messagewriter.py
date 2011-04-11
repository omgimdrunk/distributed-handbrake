import client_0_8 as amqp

class AttributeError(Exception):
    def __init__(self,value):
        self.value=value
    def __str__(self,value):
        return repr(self.value)

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
    
    def __init__(self, *args, **kwargs):
        '''Opens connection with server, establishes a channel, declares an exchange, declares a queue, and binds the queue to the exchange'''
        self._options=dict(routing_key='',  server='localhost', vhost='/',\
             userid='guest', password='guest', exchange='',\
             exchange_type='direct', exchange_durable=True, \
             exchange_auto_delete=False, queue_durable=False, \
             queue_auto_delete=True)
        
        if len(kwargs)!=0:
            self._options.update(kwargs)
        else:
            self._options.update(args[0])            
            
        if self._options['routing_key']=='':
            raise AttributeError('Routing Key must be defined')
        
        self._connection = amqp.Connection(host=self._options['server'], \
                                           userid=self._options['userid'], \
                                           password=self._options['password'], \
                                           virtual_host=self._options['vhost'])
        self._channel = self._connection.channel()
        self._channel.exchange_declare(exchange=self._options['exchange'], \
                                       type=self._options['exchange_type'], \
                                       durable=self._options['exchange_durable'], \
                                       auto_delete=self._options['exchange_auto_delete'])
        self._channel.queue_declare(queue=self._options['routing_key'], \
                                    durable=self._options['queue_durable'], \
                                    auto_delete=self._options['queue_auto_delete'])
        self._channel.queue_bind(queue=self._options['routing_key'], \
                                 exchange=self._options['exchange'], \
                                 routing_key=self._options['routing_key'])
        
    def send_message(self, message):
        '''Takes a string/pickled object and sends it to the queue'''
        msg=amqp.Message(message)
        self._channel.basic_publish(exchange=self._options['exchange'], \
                                    routing_key=self._options['routing_key'], \
                                    msg=msg)
        
    def close(self):
        '''Closes the channel and connection to the server'''
        self._channel.close()
        self._connection.close()
