#!/usr/bin/python
#
# Linux only, depends on pyinotify

WATCH_FOLDERS=['/mnt/cluster-programs/video-encode-archive',\
               '/mnt/cluster-programs/video-encode-iPod']
JOB_FOLDER='/mnt/cluster-programs/handbrake/jobs/'
ENCODE_COMMANDS=[()]

import shutil
import DVDTitle
import pyinotify

wm = pyinotify.WatchManager()

mask = pyinotify.IN_CLOSE_WRITE | pyinotify.IN_MOVED_TO

class EventHandler(pyinotify.ProcessEvent):
        def process_IN_CLOSE_WRITE(self,event):
                print("Close Write of " + event.pathname)
                shutil.move(event.pathname,JOB_FOLDER+event.name)
                DVDTitle.ProcessDVD(path=JOB_FOLDER+event.name)
        def process_IN_MOVED_TO(self,event):
                print("Moved to " + event.pathname)

handler = EventHandler()
notifier = pyinotify.Notifier(wm,handler)


wdd = wm.add_watch('/mnt/cluster-programs/video-encode-archive', mask)

notifier.loop()