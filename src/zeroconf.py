import select
import sys
import socket
import logging
import threading

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

def register_callback(sdRef, flags, errorCode, name, regtype, domain):
    if errorCode == pybonjour.kDNSServiceErr_NoError:
        print 'Registered service:'
        print '  name    =', name
        print '  regtype =', regtype
        print '  domain  =', domain


def registerService(name,regtype,port):
    port = int(port)

    sdRef = pybonjour.DNSServiceRegister(name = name,
                                         regtype = regtype,
                                         port = port,
                                         callBack = register_callback)
    
    try:
        try:
            while True:
                ready = select.select([sdRef], [], [])
                if sdRef in ready[0]:
                    pybonjour.DNSServiceProcessResult(sdRef)
        except KeyboardInterrupt:
            pass
    finally:
        sdRef.close()
            

if __name__ == '__main__':
    import time
    name='FTP'
    regtype='_ftp._tcp'
    port = int('2010')

    sdRef = pybonjour.DNSServiceRegister(name = name,
                                         regtype = regtype,
                                         port = port,
                                         callBack = register_callback)
    

    ready = select.select([sdRef], [], [],5)
    if sdRef in ready[0]:
        pybonjour.DNSServiceProcessResult(sdRef)

    time.sleep(45)
