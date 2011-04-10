import messagewriter
import sys

from config import *

writer=messagewriter.MessageWriter(server=MESSAGE_SERVER, vhost=VHOST, \
                                   userid=MESSAGE_USERID, password=MESSAGE_PWD, \
                                   exchange=EXCHANGE, exchange_type='direct', \
                                   routing_key=SERVER_COMM_QUEUE, exchange_auto_delete=False, \
                                   queue_durable=True, queue_auto_delete=False)

while True:
    try:
        msg=raw_input('Enter Message To Send:')
        writer.send_message(msg)
    except KeyboardInterrupt:
        sys.exit(0)