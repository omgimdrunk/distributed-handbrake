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
import Queue
import subprocess
import threading
import socket
import shutil

from config import * #@UnusedWildImport
from messaging import MessageReader, MessageWriter
from tail import tail
from basicFTP import FTPConnect
from newparser import * #@UnusedWildImport


logging.basicConfig(level=logging.DEBUG)

class ProcessMonitor(threading.Thread):
    '''This class takes a subprocess, logfile, and lockfile as an input
    It proceeds to monitor the subprocess' output (assumed to be a pipe)
    and writes it to the logfile when it can acquire the logfile's lock
    
    This is needed so you can access individual lines of the program's
    output.  Otherwise the file is not readable until the process has finished
    
    This is meant to be run as a thread while initial program continues its work'''
    def __init__(self, proc, filename,  lockfile):
        threading.Thread.__init__(self)
        self.proc=proc
        self.file=open(filename, 'a', 1)
        self.lockfile=lockfile
        
    def run(self):
        while self.proc.poll() is None:
            line = self.proc.stdout.readline()
            if line:
                self.lockfile.acquire()
                self.file.write(line)
                self.file.flush()
                self.lockfile.release()
        self.file.close()
        
class JobThread(threading.Thread):
    def __init__(self,command,jobname):
        self._command=command
        self._job_name=jobname
        threading.Thread.__init__(self)
        self._status_updates=MessageWriter(STATUS_WRITER)
        
    def _encode_message(self,message):
        '''Takes a message and returns a pickled tuple of the form:
        [hostname,job name, message, timestamp]'''
        return pickle.dumps([socket.gethostname(),self._job_name, message, time.asctime()])

    def run(self):
        proc = subprocess.Popen(self._command, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        
        loglock=threading.Lock()
        logfile='encodinglog-'+self._job_name+'.txt'
        log = open(logfile,'w')
        command_string=""
        for i in self._command:
            command_string += str(i) + " "
        log.write(command_string+"\n")
        log.close()

        t = ProcessMonitor(proc, logfile, loglock)
        t.start()
        
        while proc.poll() is None:
            time.sleep(10)
            loglock.acquire()
            log=open(logfile, 'rU')
            current_progress=tail(log, 1)
            log.close()
            loglock.release()
            logging.debug(current_progress)
            self._status_updates.send_message(self._encode_message(current_progress))
    

class MakeJob(object):
    def __init__(self,queue):
        self._queue=queue
        self._writer=MessageWriter(SERVER_COMM_WRITER)
    def start_job(self,message):
        reply=pickle.loads(message.body)
        logging.debug('Decoded message to '+str(reply))
        #We expect a message in the form of [job name, ftp path,[[encode command ready for subprocess],title-duratino]]
        os.chdir(CLIENT_BASE_DIR)  #@UndefinedVariable   Is added to config.py by client-deploy script       
        subprocess.call(['wget','-r','-nH','-N','--cut-dirs=1',reply[1]])
        input_name=reply[0]
        command=reply[2][0]
        duration=reply[2][1]
        command.append('-i')
        command.append(input_name)
        print("Command received: "+str(command))
        print("Duration: "+str(duration))
        #We have to scan for the local title number as this can be different from when the server scanned
        title_number=''
        print("Scanning "+str(input_name))        
        current_dvd=parseDVD(input_name)
        print(str(current_dvd))
        for title in current_dvd.titles:
            print(str(title.duration))
            if duration == title.duration:
                title_number=title.title_number
                command.append('-t')
                command.append(title.title_number)
                break
        if title_number == '':
            logging.error('Title to be encoded could not be identified')
            return        
        
        for i,item in enumerate(command):
            if item=='-o':
                output_name=command[i+1]

        logging.debug('Starting ')
        w=JobThread(command,reply[0])
        w.start()
        w.join()        
        logging.debug('Notifying reader to acknowledge message ' + str(message.delivery_tag))
        
        if os.path.isdir(input_name):
            shutil.rmtree(path=input_name,ignore_errors=True)
        else:
            try:
                os.remove(input_name)
            except:
                pass
            
        ftp_connect=FTPConnect('192.168.5.149','2010')
        ftp_connect.change_directory('output')
        file = open(output_name,'rb')
        logging.debug('Uploading output file')
        ftp_connect.upload(output_name,file)
        ftp_connect.close_connection()
        file.close()
        
        self._queue.put(message.delivery_tag)
        self._writer.send_message(reply[0]) #Have server unmount any ISOs

if __name__ == '__main__':  
    
    logging.debug('Opening message reader')
    acknowledge_queue=Queue.Queue()    
    job_writer=MakeJob(acknowledge_queue)
    
    reader=MessageReader(server='Chiana', vhost='cluster', \
                     userid='cluster-admin', password='1234', \
                     exchange='handbrake', \
                     exchange_type='direct',\
                     routing_key='job-queue',\
                     callback=job_writer.start_job,\
                     no_ack=False,\
                     ack_queue=acknowledge_queue)
    reader.setPrefetch(prefetch_limit=1)
    
    logging.debug('Opening message writer')
    writer=MessageWriter(SERVER_COMM_WRITER)
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