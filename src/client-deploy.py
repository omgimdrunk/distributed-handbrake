import os.path
from ftplib import FTP
import subprocess

filelist=['client.py','client_0_8','config.py','messaging.py','tail.py','bin_win32/HandBrakeCLI.exe']

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
        
    def chdir(self,dir):
        self._ftp.cwd(dir)
        
        
    def close_connection(self):
        self._ftp.close()

os.chdir(os.path.expanduser('~'))
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

for i in filelist:
    subprocess.call(['wget','-r','-nH','ftp://192.168.5.149:2010/'+i])