#!/usr/bin/python
#
# Linux only, depends on pyinotify which must be installed
#
# Watches a designated folder for new files and calls an encoding handler for
# any new files that appear.  Then moves them to the encoding job folder and passes
# off to encoding handler
# 
# Encoding handler is responsible for determining if the input is valid
#
#

import shutil
import os.path
import DVDTitle
import pyinotify
import logging
from config import *
import os
import subprocess
import messagereader

class EventHandler(pyinotify.ProcessEvent):
        def process_IN_CLOSE_WRITE(self,event):
                logging.debug('Close of ' + event.pathname)
                logging.debug('Moving ' + event.pathname + ' to ' + os.path.join(JOB_FOLDER,event.name))
                shutil.move(event.pathname,os.path.join(JOB_FOLDER,event.name))
                logging.debug('Spawning encode processing thread')
                DVDTitle.ProcessDVD(os.path.join(JOB_FOLDER,event.name)).start()
        def process_IN_MOVED_TO(self,event):
                logging.debug(event.pathname + ' moved to watch folder')
                logging.debug('Moving ' + event.pathname + ' to ' + os.path.join(JOB_FOLDER,event.name))
                shutil.move(event.pathname,os.path.join(JOB_FOLDER,event.name))
                logging.debug('Spawning encode processing thread')
                DVDTitle.ProcessDVD(os.path.join(JOB_FOLDER,event.name)).start()\
                
                
def ISOUmounter(message):
    '''This will be called by our message reader.  Message is a string consisting
    of a job mountpoint.'''
    os.chdir(JOB_FOLDER)
    if os.path.isdir(message.body):
        try:
            subprocess.check_call(['sudo','umount',message.body])
        except:
            logging.error('Unable to unmount ' + message.body +'. Skipping')
        else:
            logging.info('Successfully unmounted ISO, attempting to remove directory')
            try:
                subprocess.check_call(['rmdir',message.body])
            except:
                logging.error('Unable to remove directory ' + message.body +'. Skipping')
            else:
                logging.info('Successfully removed directory '+message.body)

                
umount_handler=messagereader.MessageReader(server=MESSAGE_SERVER, vhost=VHOST, \
                                           userid=MESSAGE_USERID, password=MESSAGE_PWD, \
                                           exchange=EXCHANGE, exchange_type='direct', \
                                           routing_key=SERVER_COMM_QUEUE, \
                                           callback=ISOUmounter)
umount_handler.start()
#Runs in a separate thread and waits on incoming messages

wm = pyinotify.WatchManager()
mask = pyinotify.IN_CLOSE_WRITE | pyinotify.IN_MOVED_TO
handler = EventHandler()
notifier = pyinotify.Notifier(wm,handler)

wdd = wm.add_watch(WATCH_FOLDER, mask)


notifier.loop()
