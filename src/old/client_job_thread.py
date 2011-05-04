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

import threading
import subprocess
import os
import socket
import shutil
import time
import logging
import pickle

from messaging import MessageWriter
from tail import tail

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
        self.file=open(filename, 'w', 1)
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
    '''Plan to spawn one JobThread per encoding job on the machine.
    As the jobs will be handled by external encoders, I expect that
    using a thread instead of multiple processes will be OK.
    
    Job takes the following inputs:
    project_name:    Name of the type of encode
    job_name:        Unique identifier of particular encode
    exe_name:        Name of the external program for performing encode
    command:         The command line to be passed to encoding exe
    output_file:     Name of the output file for the encode
    
    server_ip:       IP address of file server
    source_path:     Path to the source folder on file server
    destination_path: Path to destination folder on file server
    
    message_server:  IP address of RabbitMQ message server
    vhost:           Virtual Host on message server
    userid:          Message server user
    password:        Message server password
    server_hostname: Message server hostname (used for message routing)
    '''
    def __init__(self, project_name, job_name, exe_name, command, output_file, \
                 server_ip, source_path, destination_path, \
                 message_server, vhost, userid, password, server_hostname):
        threading.Thread.__init__(self)
        
        self._project_name=project_name
        self._job_name=job_name
        self._exe_name=exe_name
        self._command=command
        self._output_file=output_file
 
        self._server_ip=server_ip                       
        self._source_path=source_path
        self._destination_path=destination_path

        self._message_server=message_server
        self._vhost=vhost
        self._userid=userid
        self._password=password
        self._server_hostname=server_hostname

        
    def _encode_message(self,message):
        '''Takes a message and returns a pickled tuple of the form:
        [hostname,job name, message, timestamp]'''
        return pickle.dumps([socket.gethostname(),self._job_name, message, time.asctime()])
        
    def run(self):
        '''Creates required directories, base_dir at ~/cluster_programs/project_name
        copies source and encoder to temporary job directory, encodes the source
        uploads the resulting files to the file server, and deletes all temporary
        files.
        
        Sends status updates on encode to the message server every second'''
        
        homedir = os.path.expanduser('~')
        projectdir = os.path.join(homedir, 'cluster_programs', self._project_name)
        jobdir=os.path.join(homedir, 'cluster_programs', self._project_name, self._job_name)
        sourcedir=os.path.join('\\\\', self._server_ip,self._source_path)
        outputdir=os.path.join('\\\\', self._server_ip, self._destination_path)
        
        os.chdir(projectdir)
        try:
            os.mkdir(self._job_name)
        except OSError:
            logging.debug('Directory' + self._job_name +' exists, continuing using existing dir')
        
        shutil.copy(self._exe_name, self._job_name)
        os.chdir(jobdir)


        logging.debug('Connecting with message server')
        status_updates=MessageWriter(server=self._message_server, vhost=self._vhost, userid=self._userid, password=self._password, exchange='direct_transfer', exchange_durable=True, \
                              exchange_auto_delete=False, exchange_type='direct', routing_key=self._server_hostname, queue_durable=False, queue_auto_delete=True)
        logging.debug('Connection with message server established')
        
        logging.debug('Copying Source')                      
        status_updates.send_message(self._encode_message('Copying Source'))
        if os.path.exists('source'):
            shutil.rmtree('source')
        shutil.copytree(sourcedir, 'source')
        status_updates.send_message(self._encode_message('Finished Copying Source'))
        logging.debug('Finished Copying Source')
        
        logging.debug('Starting encode process '+self._exe_name)
        status_updates.send_message(self._encode_message('Starting Process '+self._exe_name))
        proc = subprocess.Popen(self._command, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        
        loglock=threading.Lock()
        logfile='encodinglog.txt'

        t = ProcessMonitor(proc, logfile, loglock)
        t.start()
        
        while proc.poll() is None:
            time.sleep(30)
            loglock.acquire()
            log=open(logfile, 'rU')
            current_progress=tail(log, 1)
            log.close()
            loglock.release()
            logging.debug(current_progress)
            status_updates.send_message(self._encode_message(current_progress))
            
        logging.debug('Finished Encoding')
        status_updates.send_message(self._encode_message('Finished Encoding'))
        
        logging.debug('Copying Output to Server')
        status_updates.send_message(self._encode_message('Copying Output to Server'))
        shutil.copy(self._output_file, outputdir)
        logging.debug('Finished Copying Output to Server')
        status_updates.send_message(self._encode_message('Finished Copying Output to Server'))
        
        os.chdir(homedir)
        logging.debug('Deleting temporary files and directories')
        shutil.rmtree(path=jobdir, ignore_errors=True)
        logging.debug('Closing connection with message server')
        status_updates.close()
        
if __name__ == '__main__':
    '''Creates a test thread, for debug purposes only'''
    test_thread=JobThread(project_name='test_prj',\
                          source_path='Users\Erik\cluster_test\source\\',\
                          server_ip='127.0.0.1',\
                          destination_path='Users\Erik\cluster_test\destination\\',\
                          job_name='test_job',\
                          exe_name='HandBrakeCLI.exe',\
                          command=['HandBrakeCLI.exe','-i','source','-o','test_job.mkv'],\
                          message_server='192.168.5.149',\
                          vhost='cluster',\
                          userid='cluster-admin',\
                          password='1234',\
                          server_hostname='Chiana',\
                          output_file='test_job.mkv')
    test_thread.start()
    test_thread.join()

        
        