import messagewriter
import sys

from config import *

writer=messagewriter.MessageWriter(SERVER_COMM_WRITER)

while True:
    try:
        msg=raw_input('Enter Message To Send:')
        writer.send_message(msg)
    except KeyboardInterrupt:
        sys.exit(0)