import threading
import subprocess
import os
import socket
import shutil
import time
import logging
import pickle

from client_job_thread import JobThread
from messagewriter import MessageWriter

class ProjectThread(threading.Thread):
    def __init__(self,project_name,project_dir,server_ip,message_server_ip,vhost):
        threading.Thread.__init__(self)
        
        
    # Needs a listener on vhost/project_name
    # Messages will be of form [hostname, server ip, source, destination, command]
    def _process_message(self,message):
        message_decoded=pickle.loads(str=message)
        if message_decoded=