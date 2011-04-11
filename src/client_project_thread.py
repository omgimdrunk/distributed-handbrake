import threading
import os
import socket
import shutil
import logging
import pickle

from client_job_thread import JobThread
from messaging import MessageWriter
from messaging import MessageReader


class ProjectThread(threading.Thread):
    '''Needs to listen on vhost/project-name/queue, vhost/project-name/hostname,
    and establish a write connection on vhost/project-name/server
    
    So, two messagereaders and one messagewriter
    
    Also must make the project directory, copy the encoding exe to this directory'''
    
    def __init__(self, project_name, project_exe, project_exe_path, \
                 server_ip='localhost', message_server_ip='localhost',\
                 message_server_hostname='localhost', vhost='/', userid='guest',\
                 password='guest'):
        threading.Thread.__init__(self)
        self._project_name=project_name
        self._project_exe=project_exe
        self._project_exe_path=project_exe_path
        self._server_ip=server_ip
        self._message_server_ip=message_server_ip
        self._message_server_hostname=message_server_hostname
        self._vhost=vhost
        self._userid=userid
        self._password=password
        self._running=True
        
    def run(self):
        
        homedir = os.path.expanduser('~')
        basedir = os.path.join(homedir,'cluster_programs')
        projectdir = os.path.join(homedir, 'cluster_programs', self._project_name)
        
        logging.debug('Making base directory for project '+self._project_name)
        os.chdir(basedir)
        try:
            os.mkdir(self._project_name)
        except OSError:
            logging.debug('Directory' + self._project_name +' exists, continuing using existing dir')
        os.chdir(projectdir)
        logging.debug('Base directory created at '+ projectdir)
        
        logging.debug('Copying encoding executable for '+self._project_name)
        exe_path=os.path.join('\\\\', self._server_ip,self._project_exe_path,
                              self._project_exe)
        shutil.copy(exe_path,self._project_exe)
        logging.debug('Finished copying encoding executable')

        #Establishes the direct-connect message connection with server
        #Sends messages to vhost/direct-connect/message-server-hostname
        #Messages will have form [hostname, project, message]
        self._server_direct_connect=MessageWriter(server=self._message_server_ip,\
            vhost=self._vhost,userid=self._userid,password=self._password,\
            exchange=self._project_name,exchange_type='direct',exchange_durable=True,\
            exchange_auto_delete=False,\
            routing_key=self._message_server_hostname)
        
        #Establishes a listener that will accept new jobs and spin off
        #client job threads in response
        self._project_queue_listener=MessageReader(server=self._message_server_ip,\
            vhost=self._vhost,userid=self._userid,password=self._password,\
            exchange=self._project_name,routing_key='queue',exchange_type='direct',\
            callback=self._job_creation)
        
        #Establishes a listener that will accept direct messages from server
        #and respond appropriately
        self._project_server_listener=MessageReader(server=self._message_server_ip,\
            vhost=self._vhost,userid=self._userid,password=self._password,\
            exchange=self._project_name,routing_key=socket.gethostname(),\
            exchange_type='direct',callback=self._process_message)
        
        self._project_queue_listener.start()
        self._project_server_listener.start()
        
        while self._running==True:
            pass
        #Still need to work out message acknowledgment.  Will probably do so with
        #a queue.  Currently, acknowledgment is turned off, which is not ideal
        
        self._project_queue_listener.stop()
        self._project_server_listener.stop()
        self._server_direct_connect.close()
        
        self._project_queue_listener.join()
        self._project_server_listener.join()
        
        
    # Needs a listener on vhost/project_name
    # Messages will be of form [hostname, server ip, source, destination, command]
    def _process_message(self,message):
        pass
        #Currently all communication is one directional
        
    def _job_creation(self,message):
        '''Note: does not keep track of threads as I currently don't have a way
        of stopping a job thread'''
        cmd=pickle.loads(str=message)
        #[job_name, source_path, destination_path, [command], output_file]
        job=JobThread(project_name=self._project_name, job_name=cmd[0], exe_name=self._project_exe,\
                    source_path=cmd[1], destination_path=cmd[2], command=cmd[3],\
                    output_file=cmd[4],\
                    message_server=self._message_server_ip,\
                    vhost=self._vhost, userid=self._userid, password=self._password,\
                    server_hostname=self._message_server_hostname,\
                    server_ip=self._server_ip)
        job.start()
    
    def stop(self):
        self._running=False
    
    
        
        
