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


import os.path
import shutil
import logging
import time
import subprocess
import platform
import sys
import threading

try:
    from pyftpdlib import ftpserver
except:
    sys.exit('pyftpdlib must be installed')

if platform.system()=='Linux':
    try:
        import pyinotify #@UnresolvedImport
    except:
        sys.exit('pyinotify must be installed')
else:
    sys.exit('Only Linux is supported as a server')

from config import * #@UnusedWildImport
#import DVDTitle
import jobGenerator
import messaging

logging.basicConfig(level=logging.DEBUG)

class ServeFTP(threading.Thread):
    
    def __init__(self, path='.', ip='127.0.0.1', port='21'):
        threading.Thread.__init__(self)
        self._path=path
        self._ip=ip
        self._port=port
        self._running=True

    def run(self):
        logging.debug('Starting FTP server on ' + str(self._ip) + ':' + str(self._port) + ' with root '\
                      + self._path)
        os.chdir(self._path)
        authorizer = ftpserver.DummyAuthorizer()
        authorizer.add_anonymous(homedir='.',perm='elradfmw')
    
        handler = ftpserver.FTPHandler
        handler.authorizer = authorizer
    
        address = (self._ip, self._port) #Can use 0.0.0.0 to listen on all interfaces/IPs
        server = ftpserver.FTPServer(address, handler)
    
        server.max_cons = 256
        server.max_cons_per_ip = 5
        
        while self._running:
            server.serve_forever(count=1)
            
        logging.debug('FTP Server successfully stopped')
        
    def stop(self):
        logging.debug('Stopping FTP Server')
        self._running=False


class EventHandler(pyinotify.ProcessEvent):
        def process_default(self,event):
                if event.path==WATCH_FOLDER:
                    return
                time.sleep(1)
                try:                
                    logging.debug('Moving ' + event.pathname + ' to ' + os.path.join(JOB_FOLDER,event.name))
                    shutil.move(event.pathname,os.path.join(JOB_FOLDER,event.name))
                except IOError:
                    logging.error(os.path.join(event.pathname+' does not exist'))
                    return
                for directory in CONVERSION_TYPES:
                    if directory in event.path:
                        logging.debug('Spawning encode processing thread')
                        jobGenerator.ProcessDVD(os.path.join(JOB_FOLDER,event.name),directory.replace('-','_')).start()

                
                
def ISOUmounter(message):
    '''This will be called by our message reader.  Message is a string consisting
    of a job mountpoint.'''
    logging.debug('Recieved message ' + str(message))
    logging.debug('Changing directory to ' + JOB_FOLDER)
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

             
umount_handler=messaging.MessageReader(server=MESSAGE_SERVER, vhost=VHOST, \
                                       userid=MESSAGE_USERID, password=MESSAGE_PWD, \
                                       exchange=EXCHANGE, exchange_type='direct', \
                                       routing_key=SERVER_COMM_QUEUE, \
                                       callback=ISOUmounter)
def main():
    try:
        os.mkdir(WATCH_FOLDER)
    except OSError:
        logging.debug('Watch folder already exists')
    for i in CONVERSION_TYPES:
        try:
            os.mkdir(os.path.join(WATCH_FOLDER,i))
        except OSError:
            logging.debug('Conversion folder ' + i + ' already exists')
    
    umount_handler.start()
    
    ftpshare=ServeFTP(BASE_DIR,'0.0.0.0',FTP_PORT)
    ftpshare.start()
    
    wm = pyinotify.WatchManager()
    mask = pyinotify.IN_CLOSE_WRITE | pyinotify.IN_MOVED_TO
    handler = EventHandler()
    notifier = pyinotify.ThreadedNotifier(wm,handler)
    wdd = wm.add_watch(WATCH_FOLDER, mask, rec=True)
    notifier.start()
    
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            notifier.stop()
            umount_handler.stop()
            ftpshare.stop()
            print('\nUser Requested Stop\n')
            break
        except:
            notifier.stop()
            umount_handler.stop()
            ftpshare.stop()
            break

if __name__ == '__main__':
    main()