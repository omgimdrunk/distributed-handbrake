import threading
import time
import logging
from amqplib import client_0_8 as amqp

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
            cur_message=self.channel.basic_get()
            if cur_message != None:
                logging.debug('Calling ' + str(self.callback) + ' with message '+\
                              str(cur_message))
                self.callback(cur_message)
            time.sleep(1)
            #I am using basic_get() instead of wait() because the latter seems to
            #never return, therefore the while loop only checks its status one time
            
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
    
    def printOutput(message):
        print "Message received: "+message.body
    
    a=MessageReader(server, vhost, userid, password, exchange, exchange_type, routing_key, printOutput)
    logging.debug('Starting reader thread')
    a.start()
    logging.debug('Sleeping')
    time.sleep(5)
    logging.debug('Stopping reader thread')
    a.stop()
    logging.debug('Exiting')
