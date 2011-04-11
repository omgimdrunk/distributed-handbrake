#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import messaging
import sys

from config import *

writer=messaging.MessageWriter(SERVER_COMM_WRITER)

while True:
    try:
        msg=raw_input('Enter Message To Send:')
        writer.send_message(msg)
    except KeyboardInterrupt:
        sys.exit(0)