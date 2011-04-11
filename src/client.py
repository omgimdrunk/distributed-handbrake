#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import platform
import os.path
import sys
import logging
import time
import pickle

from config import * #@UnusedWildImport
from messaging import MessageReader, MessageWriter


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
    reply=pickle.loads(message.body)
    logging.debug('Decoded to '+str(reply))
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
writer=MessageWriter(server=MESSAGE_SERVER, vhost=VHOST, \
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