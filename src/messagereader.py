from amqplib import client_0_8 as amqp

class MessageReader(object):
    '''Gets a message from a RabbitMQ server'''
    
    def __init__(self, server, vhost, userid, password, exchange, exchange_type, routing_key, callback):
        self.server=server
        self.vhost=vhost
        self.userid=userid
        self.password=password
        self.exchange=exchange
        self.routing_key=routing_key
        self.exchange_type=exchange_type
        self.callback=callback
        
        self.connection = amqp.Connection(host=self.server, userid=self.userid, password=self.password, virtual_host=self.vhost)
        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange=self.exchange, type=self.exchange_type, durable=True, auto_delete=False)
        self.channel.queue_declare(queue=self.routing_key, durable=True, auto_delete=False)
        self.channel.queue_bind(queue=self.routing_key, exchange=self.exchange,  routing_key=self.routing_key)
        
        self.channel.basic_consume(queue=self.routing_key, no_ack=True, callback=self.callback)
        
    def wait(self):
        while True:
            self.channel.wait()
            


if __name__ == '__main__':    
    server='192.168.5.149'
    vhost='videos'
    userid='videos'
    password='1234'
    exchange='video_exchange'
    exchange_type='direct'
    routing_key='to_encode'
    
    def printOutput(message):
        print "Message received: "+message.body
    
    a=MessageReader(server, vhost, userid, password, exchange, exchange_type, routing_key, printOutput)
    a.wait()
