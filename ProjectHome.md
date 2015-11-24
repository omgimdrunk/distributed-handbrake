This is a collections of scripts that form a server and a client for a distributed video encoding system based on HandBrakeCLI.  They are written in Python and assume that the server is Linux-based (depends on pyinotify).  The client can/will be either Linux or Windows (support for MacOS X should be simple as well).

The overall goal is to have several watch-folders into which you can drop ISOs or avi/mp4/mkv files and have them encoded to various other formats.  The encoding is distributed to other systems on the network.  This is done by using RabbitMQ to pass messages between the server and clients.

This project is currently in the early implementation stages.

I am using Aptana Studio with PyDev for development.