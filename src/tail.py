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

import os

def tail( file, lines_to_find=5 ):
    '''Utility function that takes a file descriptor open for reading and an
    integer and returns that number of lines from the end of the file'''
    
    file.seek( 0, os.SEEK_SET )       #Seek to the end of the file
    bytes = file.tell() #Check the size of the entire file
    
    if bytes < 1024:    #File is less than our chunk size
        file.seek(0)    #scan to the beginning of file
        lines = file.readlines()  #And read all lines
        if lines < lines_to_find:
            return lines
        else:
            return lines[-lines_to_find:]
    else:
        lines_found = 0
        block = 1              #Will be scanning backward in the file in 1024 byte chunks
        while lines_found < lines_to_find + 1 and bytes-block*1024  > 0:
            #We need to find one more line than requested as we will be using
            #readline to make sure only to return full lines
            file.seek( -block*1024, 2 )
            data = file.read( 1024 )
            lines_this_block= data.count('\n')
            lines_found += lines_this_block
            block += 1
        block -= 1  #We will have incremented block one too many times in the loop
        file.seek( -block*1024, 2 )
        file.readline() #Move to the end of the last line found.
        #OK because we are guaranteed to have found at least one more \n than necessary
        lines = file.readlines()
        return lines[-lines_to_find:]

if __name__ == '__main__':
    f=open('config.py','r')
    print(tail(f,9))
    f.close()