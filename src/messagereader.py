import threading
import time
import logging
import client_0_8 as amqp

from config import *

logging.basicConfig(level=logging.DEBUG)

class MessageReader(threading.Thread):
    '''Gets a message from a RabbitMQ server'''
    
    def __init__(self, *args, **kwargs):
        threading.Thread.__init__(self)
        self._options=dict(server='localhost',vhost='/',userid='guest',password='guest',\
                           exchange='',exchange_type='direct',exchange_durable=True,\
                           exchange_auto_delete=False,routing_key='',queue_durable=True,\
                           queue_auto_delete=False,no_ack=True,callback='')
        self._running=True
        if len(kwargs)!=0:
            self._options.update(kwargs)
        else:
            self._options.update(args[0])
        if self._options['routing_key']=='':
            raise AttributeError('Routing Key must be defined')

    def run(self):        
        self._connection = amqp.Connection(use_threading=True,\
                                          host=self._options['server'], \
                                          userid=self._options['userid'], \
                                          password=self._options['password'], 
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
        
        self._channel.basic_consume(queue=self._options['routing_key'], \
                                   no_ack=self._options['no_ack'], \
                                   callback=self._options['callback'])

        while self._running:
            try:
                self._channel.wait(timeout=float('1'))
            except amqp.Timeout:
                pass
            
        logging.debug('closing channel')
        self._channel.close()
        logging.debug('closing connection')
        self._connection.close()
        logging.debug('exiting thread')

    def stop(self):
        logging.debug('Setting running to false')
        self._running=False


if __name__ == '__main__':    
    server='192.168.5.149'
    vhost='cluster'
    userid='cluster-admin'
    password='1234'
    exchange='handbrake'
    exchange_type='direct'
    routing_key='job-queue'
    
    def printOutput(msg):
        logging.debug('Message received')
        print "Message received: "+msg.body
    
    a=MessageReader(server=MESSAGE_SERVER, vhost=VHOST, \
                    userid=MESSAGE_USERID, password=MESSAGE_PWD, \
                    exchange=EXCHANGE, exchange_type='direct', \
                    routing_key=SERVER_COMM_QUEUE, callback=printOutput)
    
    
    import messagewriter
    writer=messagewriter.MessageWriter(server=MESSAGE_SERVER, vhost=VHOST, \
                                   userid=MESSAGE_USERID, password=MESSAGE_PWD, \
                                   exchange=EXCHANGE, exchange_type='direct', \
                                   routing_key=SERVER_COMM_QUEUE, exchange_auto_delete=False, \
                                   queue_durable=True, queue_auto_delete=False)
    writer.send_message('Test')
    time.sleep(10)
    logging.debug('Starting reader thread')
    a.start()
    writer.send_message('Sleeping')
    logging.debug('Sleeping')
    time.sleep(5)
    writer.send_message('Getting ready to stop reader thread')
    time.sleep(1)
    logging.debug('Stopping reader thread')
    a.stop()
    logging.debug('Exiting')
