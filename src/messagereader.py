import threading
import time
import logging
import client_0_8 as amqp

from config import *

logging.basicConfig(level=logging.DEBUG)

class MessageReader(threading.Thread):
    '''Gets a message from a RabbitMQ server'''
    
    def __init__(self, server, vhost, userid, password, exchange, exchange_type, routing_key, callback):
        threading.Thread.__init__(self)
        self.server=server
        self.vhost=vhost
        self.userid=userid
        self.password=password
        self.exchange=exchange
        self.routing_key=routing_key
        self.exchange_type=exchange_type
        self.callback=callback
        self._running=True

    def run(self):        
        self.connection = amqp.Connection(use_threading=True,host=self.server, userid=self.userid, password=self.password, virtual_host=self.vhost)
        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange=self.exchange, type=self.exchange_type, durable=True, auto_delete=False)
        self.channel.queue_declare(queue=self.routing_key, durable=True, auto_delete=False)
        self.channel.queue_bind(queue=self.routing_key, exchange=self.exchange,  routing_key=self.routing_key)
        
        self.channel.basic_consume(queue=self.routing_key, no_ack=True, callback=self.callback)

        while self._running:
            try:
                self.channel.wait(timeout=float('1'))
            except amqp.Timeout:
                pass
            
        logging.debug('closing channel')
        self.channel.close()
        logging.debug('closing connection')
        self.connection.close()
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
