#!/usr/bin/python
#
#Stors the configuration information that will be used across entire project
#

WATCH_FOLDER='/mnt/cluster-programs/video-encode-archive'
JOB_FOLDER='/mnt/cluster-programs/handbrake/jobs/'

MESSAGE_SERVER='Chiana'
VHOST='cluster'
MESSAGE_USERID='cluster-admin'
MESSAGE_PWD='1234'
EXCHANGE='handbrake'
JOB_QUEUE='job-queue'
SERVER_COMM_QUEUE='server-queue'


SERVER_COMM_WRITER=dict(server=MESSAGE_SERVER, vhost=VHOST, \
                        userid=MESSAGE_USERID, password=MESSAGE_PWD, \
                        exchange=EXCHANGE, exchange_type='direct', \
                        routing_key=SERVER_COMM_QUEUE, exchange_auto_delete=False, \
                        queue_durable=True, queue_auto_delete=False)

