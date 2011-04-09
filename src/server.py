#!/usr/bin/python
#
# Linux only, depends on pyinotify which must be installed
#
# Watches a designated folder for new files and calls an encoding handler for
# any new files that appear.  Then moves them to the encoding job folder and passes
# off to encoding handler
# 
# Encoding handler is responsible for determining if the input is valid

import shutil
import os.path
import DVDTitle
import pyinotify
import logging
from config import *


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
                DVDTitle.ProcessDVD(os.path.join(JOB_FOLDER,event.name)).start()
                
wm = pyinotify.WatchManager()
mask = pyinotify.IN_CLOSE_WRITE | pyinotify.IN_MOVED_TO
handler = EventHandler()
notifier = pyinotify.Notifier(wm,handler)

wdd = wm.add_watch(WATCH_FOLDER, mask)
notifier.loop()
