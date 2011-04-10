import platform
import os.path
import sys
import logging
import time
import pickle

from config import *
from messagereader import MessageReader
import messagewriter

logging.basicConfig(level=logging.DEBUG)

JOB_DIR=''
if platform.system()=='Windows':
    JOB_DIR=os.path.join('\\\\','192.168.5.149','cluster-programs','handbrake','jobs')
elif platform.system()=='Linux':
    JOB_DIR=os.path.join('/','mnt','cluster-program','handbrake','jobs')
else:
    sys.exit('Only Windows and Linux are supported clients')
    
logging.debug('JOB_DIR set to '+JOB_DIR)

def MakeJob(message):
    logging.debug('Got message '+str(message.body))
    reply=pickle.dumps(message.body)
    logging.debug('Sending message '+str(reply[0]))
    writer.send_message(reply[0])

logging.debug('Opening message reader')    
reader=MessageReader(server='Chiana', vhost='cluster', \
                 userid='cluster-admin', password='1234', \
                 exchange='handbrake', \
                 exchange_type='direct',\
                 routing_key='job-queue',\
                 callback=MakeJob)

logging.debug('Opening message writer')
writer=messagewriter.MessageWriter(server=MESSAGE_SERVER, vhost=VHOST, \
                                   userid=MESSAGE_USERID, password=MESSAGE_PWD, \
                                   exchange=EXCHANGE, exchange_type='direct', \
                                   routing_key=SERVER_COMM_QUEUE, exchange_auto_delete=False, \
                                   queue_durable=True, queue_auto_delete=False)

logging.debug('Starting reader')
reader.start()


while True:
    try:
        time.sleep(1)
    except KeyboardInterrupt:
        reader.stop()
        writer.close()
        print('\nUser Requested Stop\n')
        break
    except:
        reader.stop()
        writer.close()
        break