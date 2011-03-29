#!/usr/bin/python

import threading

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