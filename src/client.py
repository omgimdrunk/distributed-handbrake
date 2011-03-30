import platform
import os.path
import sys
import logging
from messagereader import MessageReader

JOB_DIR=''
if platform.system()=='Windows':
    JOB_DIR=os.path.join('\\\\','192.168.5.149','cluster-programs','handbrake','jobs')
elif platform.system()=='Linux':
    JOB_DIR=os.path.join('/','mnt','cluster-program','handbrake','jobs')
else:
    sys.exit('Only Windows and Linux are supported clients')

def MakeJob(message):
    pass
    
reader=MessageReader(server='Chiana', vhost='cluster', \
                 userid='cluster-admin', password='1234', \
                 exchange='handbrake', \
                 exchange_type='direct',\
                 routing_key='job-queue',\
                 callback=MakeJob)