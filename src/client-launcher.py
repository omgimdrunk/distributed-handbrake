import subprocess
import os
from config import *

os.chdir(CLIENT_BASE_DIR)  #@UndefinedVariable 
subprocess.call(['wget','-N','-nd','ftp://192.168.5.149:2010/client_files.py'])
from client_files import *

for i in filelist:
    subprocess.call(['wget','-r','-N','-nd','ftp://192.168.5.149:2010/'+i])
    
for i in folderlist:
    subprocess.call(['wget','-r','-N','-nH','ftp://192.168.5.149:2010/'+i])
    
file = open('config.py','a+')
file.write('CLIENT_BASE_DIR=\'' + os.getcwd() + '\'\n')
file.close()

subprocess.Popen(['python','client.py'], shell=True)