from ftplib import FTP

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
        
    def upload(self,filename,infile):
        g=open(filename,"rb")
        self._ftp.storbinary("STOR "+filename,g)
        g.close
        
    def change_directory(self,directory):
        self._ftp.cwd(directory)
        
    def close_connection(self):
        self._ftp.close()