#!/usr/bin/python
#
#Stores the configuration information that will be used across entire project
#
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

