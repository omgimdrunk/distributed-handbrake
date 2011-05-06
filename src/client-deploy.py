import os.path
from ftplib import FTP
import subprocess

class FTPConnect(object):
    def __init__(self,host='localhost',port='21',username='anonymous',password=None):
        self._host=host
        self._port=port
        self._username=username
        self._password=password
        self._ftp = FTP()
        self._ftp.connect(self._host,self._port)
        if self._username=='anonymous':
            self._ftp.login()
        else:
            self._ftp.login(self._username,self._password)
            
    def download(self,filename,outfile):
        self._ftp.retrbinary("RETR "+filename,outfile.write)
        
    def close_connection(self):
        self._ftp.close()


        
print("Input the base directory for temporary storage.  Make sure it has a large quantity of free space.")
print("Default is "+os.path.expanduser('~'))

while True:
    clientBaseDir = raw_input('-->')
    if clientBaseDir == '':
        clientBaseDir=os.path.expanduser('~')
    if os.path.exists(clientBaseDir) and os.path.isdir(clientBaseDir):
        os.chdir(clientBaseDir)
        break
    elif os.path.exists(clientBaseDir) and os.path.isdir(clientBaseDir)==False:
        print("You must enter a valid, absolute, temporary directory")
    elif os.path.exists(clientBaseDir)==False:
        try:
            os.mkdir(clientBaseDir)
            os.chdir(clientBaseDir)
            break
        except:
            print("Invalid directory entered.  Choose another temporary directory")
    else:
        print("Invalid directory path.  Please enter the full absolute path to a directory you have write access to")
        
try:
    os.mkdir('cluster')
except:
    pass
os.chdir('cluster')

print("Opening connection with server")
ftp = FTPConnect('192.168.5.149','2010')
print("Downloading wget")
file = open('wget.exe','wb')
ftp.download('bin_win32/wget.exe',file)
file.close()
ftp.close_connection()

print("Using wget to download remaining files")

subprocess.call(['wget','-N','-nd','ftp://192.168.5.149:2010/client_files.py'])
execfile('client_files.py')

for i in filelist:
    subprocess.call(['wget','-r','-N','-nd','ftp://192.168.5.149:2010/'+i])
    
for i in folderlist:
    subprocess.call(['wget','-r','-N','-nH','ftp://192.168.5.149:2010/'+i])
    
file = open('config.py','a+')
file.write('CLIENT_BASE_DIR=\'' + os.getcwd() + '\'\n')
file.close()