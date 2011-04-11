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
    
import os
import re
import socket
import hashlib

from messaging import MessageWriter

homedir = os.path.expanduser('~')
programdir=os.path.join(homedir, 'cluster_programs')
if os.path.exists(programdir)==False:
    os.mkdir(programdir)

class ClusterProject(object):
    '''Is used to store the information about a particular project
    The items stored are the relative path, the project name, 
    the project version, and all project program files'''
    def __init__(self, path):
        self.program_files=[]
        self.path=path
        self.base_name=path
        self.version=''
        

def ScanForProjects(base_directory):

    projects=[]
    # We now read in all directories below our basedir, create project objects for them
    # and populate these objects with all .py files and the main program's version
    for project in os.listdir(base_directory):
        current_project=ClusterProject(project)
        project_listing=os.listdir(os.path.join(base_directory, project))
        for i in project_listing:
            name, extension = os.path.splitext(i)
            if extension != '':
                f=open(os.path.join(base_directory,project, i), 'rb')
                file_contents=f.read()
                f.close()
                current_project.program_files.append([i, hashlib.md5(file_contents).hexdigest()])
            m=re.search(current_project.base_name+'_([0-9][0-9]*\.[0-9][0-9]*)',name)
            if m!=None:
                current_project.version=m.group(1)
        projects.append(current_project)
        
    return projects
    

server='192.168.5.149'
vhost='cluster'
userid='cadmin'
password='1234'
hostname=socket.gethostname()

projects=ScanForProjects(programdir)
broadcast=MessageWriter(server=server, vhost=vhost, userid=userid, password=password, exchange='broadcast', exchange_durable=True, \
                        exchange_auto_delete=False, exchange_type='fanout',  routing_key=hostname, queue_durable=False, queue_auto_delete=True)
direct_transfer=MessageWriter(server=server, vhost=vhost, userid=userid, password=password, exchange='direct_transfer', exchange_durable=True, \
                              exchange_auto_delete=False, exchange_type='direct', routing_key=hostname, queue_durable=False, queue_auto_delete=True)

