import os.path
from ftplib import FTP
import subprocess
import imp
import select
import sys
import socket
import logging

import pybonjour


def getIPPort(service_name,timeout=5):
    ip_to_return=[]
    port_to_return=[]

    queried  = []
    resolved = [] 
    
    def query_record_callback(sdRef, flags, interfaceIndex, errorCode, fullname,
                              rrtype, rrclass, rdata, ttl):
        if errorCode == pybonjour.kDNSServiceErr_NoError:
            logging.debug('  IP         =', socket.inet_ntoa(rdata))
            ip_to_return.append(socket.inet_ntoa(rdata))
            queried.append(True)
    
    def resolve_callback(sdRef, flags, interfaceIndex, errorCode, fullname,
                         hosttarget, port, txtRecord):
        if errorCode != pybonjour.kDNSServiceErr_NoError:
            return
    
        logging.debug( 'Resolved service:')
        logging.debug( '  fullname   =', fullname)
        logging.debug( '  hosttarget =', hosttarget)
        logging.debug( '  port       =', port)
        
        port_to_return.append(port)
        
        query_sdRef = \
            pybonjour.DNSServiceQueryRecord(interfaceIndex = interfaceIndex,
                                            fullname = hosttarget,
                                            rrtype = pybonjour.kDNSServiceType_A,
                                            callBack = query_record_callback)
    
        try:
            while not queried:
                ready = select.select([query_sdRef], [], [], timeout)
                if query_sdRef not in ready[0]:
                    logging.debug( 'Query record timed out')
                    break
                pybonjour.DNSServiceProcessResult(query_sdRef)
            else:
                queried.pop()
        finally:
            query_sdRef.close()
    
        resolved.append(True)
    
    def browse_callback(sdRef, flags, interfaceIndex, errorCode, serviceName,
                        regtype, replyDomain):
        if errorCode != pybonjour.kDNSServiceErr_NoError:
            return
    
        if not (flags & pybonjour.kDNSServiceFlagsAdd):
            logging.debug( 'Service removed')
            return
    
        logging.debug( 'Service added; resolving')
    
        resolve_sdRef = pybonjour.DNSServiceResolve(0,
                                                    interfaceIndex,
                                                    serviceName,
                                                    regtype,
                                                    replyDomain,
                                                    resolve_callback)
    
        try:
            while not resolved:
                ready = select.select([resolve_sdRef], [], [], timeout)
                if resolve_sdRef not in ready[0]:
                    logging.debug( 'Resolve timed out')
                    break
                pybonjour.DNSServiceProcessResult(resolve_sdRef)
            else:
                resolved.pop()
        finally:
            resolve_sdRef.close()
    
    
    browse_sdRef = pybonjour.DNSServiceBrowse(regtype = service_name,
                                              callBack = browse_callback)
    
    try:
        ready = select.select([browse_sdRef], [], [],timeout)
        if browse_sdRef in ready[0]:
            pybonjour.DNSServiceProcessResult(browse_sdRef)
    finally:
        browse_sdRef.close()
        
    return(ip_to_return,port_to_return)

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

(ip,port)=getIPPort('_ftp._tcp')
print("Opening connection with server")
ftp = FTPConnect(str(ip[0]),str(port[0]))
print("Downloading ncftpget")
file = open('ncftpget.exe','wb')
ftp.download('bin_win32/ncftpget.exe',file)
file.close()
ftp.close_connection()

print("Using ncftpget to download remaining files")

subprocess.call(['ncftpget','ftp://'+str(ip[0])+':'+str(port[0])+'/client_files.py'])
execfile('client_files.py')

for i in filelist:
    subprocess.call(['ncftpget','ftp://'+str(ip[0])+':'+str(port[0])+'/'+i])
    
for i in folderlist:
    subprocess.call(['ncftpget','-R','ftp://'+str(ip[0])+':'+str(port[0])+'/'+i])
    
file = open('config.py','a+')
file.write('CLIENT_BASE_DIR=\'' + os.getcwd() + '\'\n')
file.close()