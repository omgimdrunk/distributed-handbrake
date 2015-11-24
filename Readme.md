# Introduction #

This code is in early testing only.  Currently only the server is working, though I hope to get the client running shortly.


# Details #

## Requirements ##
  * Linux for server. Kernel must have inotify support
  * Python 2.6 (should work with 2.7 as well)
  * HandBrakeCLI installed in search path
  * Ability to use the commands 'sudo mount' and 'sudo umount' without a password. (Yes, I know, I shouldn't do that, but there's only so much fighting with permissions I want to do)
  * Write permissions to /mnt/cluster-programs

For now I am hard-coding a number of the directories.  Server watch-folder is /mnt/cluster-programs/video-encode-archival, job folder is /mnt/cluster-programs/jobs, and local temporary files will be stored at ~/cluster-programs/handbrake.  Server IP is 192.168.5.149.  RabbitMQ is configured with user server-admin who has a password 1234.

Currently the working portion of this script collection is server.py, messagewriter.py, and DVDTitle.py.