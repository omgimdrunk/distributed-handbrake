Distributed Handbrake is designed to allow video encoding jobs to be sent to 
multiple computers on a network.  It consists of a server, designed to be run on
a Linux machine, and a client, which can run on either Linux or Windows.  
Upon starting, the server will create a watch folder with subfolders for each 
different encode setting.  This watch folder must be accessable to submitting 
clients in some way (NFS/SMB/CIFS/FTP etc).  The submitting client copies a 
video file or ISO to the desired encode-setting folder, the server scans the 
file, generates an appropriate encode command, and passes the file and command 
to one of the encoding clients.

This program is assumed to be operating in a trusted environment.  There are 
very minmal security settings and, as such, should not be deployed in a 
production environment.

This program is licensed under the GPL version 3.  It includes binary 
distributions of HandBrakeCLI, which is licensed under the GPL version 2, 
source available at http://handbrake.fr, and NcFTPGet, which is licensed under 
the GPL compatible Clarified Artistic License, available from 
http://www.ncftp.com.  It also includes a patched version of pyamqplib, licensed
under the GPL version 2.1 or later, available from 
https://code.google.com/p/py-amqplib/.