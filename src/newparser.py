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

import subprocess
import re
import datetime
import logging
import io
import os.path


logging.basicConfig(level=logging.ERROR)

class DVD(object):
    def __init__(self):
        self.titles=[]
        self.name=''
        self.title=''
    def __str__(self):
        formatted="DVD filename is: "+self.name+'\n'+\
        "DVD Title is: "+self.title+'\n'
        for i in self.titles:
            formatted=formatted+str(i)+'\n'
        return formatted
        
class Title(object):
    def __init__(self):
        self.title_number=''
        self.duration=datetime.timedelta(hours=0)
        self.audio_tracks=[]
        self.subtitles=[]
    def __str__(self):
        formatted="Title number "+self.title_number+":" + '\n'+\
        "    Duration: "+str(self.duration)+'\n'
        for i in self.audio_tracks:
            formatted=formatted+str(i)
        for i in self.subtitles:
            formatted=formatted+str(i)
        return formatted
        
class AudioTrack(object):
    def __init__(self):
        self.track_number=''
        self.language=''
        self.language_code=''
        self.codec=''
        self.channels=''
        self.sample_rate=''
        self.bitrate=''
    def __str__(self):
        formatted="Audio Track number "+self.track_number+":" +'\n'+\
        "    Language: "+self.language +'\n'+\
        "    Language Code: "+self.language_code +'\n'+\
        "    Codec: "+self.codec +'\n'+\
        "    Channels: "+self.channels +'\n'+\
        "    Sample Rate: "+self.sample_rate+"Hz" +'\n'+\
        "    Bitrate: "+self.bitrate+"bps" +'\n'
        return formatted
        
class Subtitle(object):
    def __init__(self):
        self.track_number=''
        self.language=''
        self.language_code=''
        self.type=''
        
    def __str__(self):
        formatted="Subtitle track "+self.track_number+":" +'\n'+\
        "    Language: "+self.language +'\n'+\
        "    Language_code: "+self.language_code +'\n'+\
        "    Type: " + self.type +'\n'
        return formatted
    
def isAudioTrack(line):
    if re.match('\+ ([0-9][0-9]*), ([A-Za-z0-9,_]*) \(([a-zA-Z0-9_ ]*)\) \(([a-zA-Z0-9_. ]*)\)',line) is None:
        return False
    else:
        return True
    
def parseAudioTrack(current_line):
    current_track=AudioTrack()       
    trackinfo=re.match('\+ ([0-9][0-9]*), ([A-Za-z0-9,_]*) \(([a-zA-Z0-9_ ]*)\) \(([a-zA-Z0-9_. ]*)\)',current_line)
    iso639_2=re.search('iso639-2: ([a-zA-Z]*)\)',current_line)
    samples=re.search('([0-9]*)Hz',current_line)
    bitrate=re.search('([0-9]*)bps',current_line)

    current_track.track_number=trackinfo.group(1)
    current_track.language=trackinfo.group(2)
    current_track.codec=trackinfo.group(3)
    current_track.channels=trackinfo.group(4)
    if iso639_2 is not None:
        current_track.language_code=iso639_2.group(1)
    if samples is not None:
        current_track.sample_rate=samples.group(1)
    if bitrate is not None:
        current_track.bitrate=bitrate.group(1)
        
    return current_track
        
def isSubtitleTrack(current_line):
    if re.match('\+ ([0-9][0-9]*), ([A-Za-z0-9,]*) \([a-zA-Z0-9\-: ]*\) \(([a-zA-Z]*)\)\(([a-zA-Z0-9\-]*)\)',current_line) is None:
        return False
    else:
        return True
    
def parseSubtitleTrack(current_line):
    current_subtitle=Subtitle()
    m=re.match('\+ ([0-9][0-9]*), ([A-Za-z0-9, ]*) \(.*\) \(([a-zA-Z]*)\)\(([a-zA-Z0-9\-]*)\)',current_line)
    iso639_2=re.search('\(iso639-2: ([a-zA-Z]*)\)',current_line)
    
    current_subtitle.track_number=m.group(1)
    current_subtitle.language=m.group(2)
    current_subtitle.type=m.group(4)
    if iso639_2 is not None:
        current_subtitle.language_code=iso639_2.group(1)
    
    return current_subtitle

def parseDVD(filename):
    current_dvd=DVD()
    current_dvd.name=filename
    
    p = subprocess.Popen( ['HandBrakeCLI','-i',filename,'-t','0'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (output,_)=p.communicate()
    
    output_file=io.StringIO(output)
    output_file.seek(0)
    current_line=output_file.readline().strip()

    while current_line.startswith('+')==False and current_line!='HandBrake has exited.':        #Advance through output until we reach summary section
        m = re.match('libdvdnav: DVD Title: (.*)',current_line)
        if m != None:
            current_dvd.title=m.group(1)
        current_line=output_file.readline().strip()
        
    if current_dvd.title=='':
        (_,lone_filename)=os.path.split(filename)
        (current_dvd.title,_)=os.path.splitext(lone_filename)

    while current_line!='HandBrake has exited.':
        current_title=Title()
        #Have a line in the format '+ title #:'
        m = re.match('\+ title ([0-9][0-9]*)',current_line)
        if m is None:
            current_line=output_file.readline().strip()
            continue
        else:
            current_title.title_number=m.group(1)
        
        current_line=output_file.readline().strip()
        while re.match('\+ duration: ([0-9][0-9]):([0-9][0-9]):([0-9][0-9])',current_line) is None:
            current_line=output_file.readline().strip()
        m = re.match('\+ duration: ([0-9][0-9]):([0-9][0-9]):([0-9][0-9])',current_line)
        current_title.duration=datetime.timedelta(hours=int(m.group(1)),minutes=int(m.group(2)),seconds=int(m.group(3)))
        
        current_line=output_file.readline().strip() #Skip forward to audio tracks section
        while re.match('\+ audio tracks:',current_line) is None:
            current_line=output_file.readline().strip()
        current_line=output_file.readline().strip() #Defines the first audio track, presumably
        
        while isAudioTrack(current_line) is True:
            current_track=parseAudioTrack(current_line)   
            current_title.audio_tracks.append(current_track)
            current_line=output_file.readline().strip()
            
        #When we get here we have gone through all this title's audio tracks and current_line
        #will have the value '+ subtitle tracks:'
        current_line=output_file.readline().strip() #Read either the first subtitle or the next title
        
        while isSubtitleTrack(current_line) is True:
            current_subtitle=parseSubtitleTrack(current_line)                
            current_title.subtitles.append(current_subtitle)
            current_line=output_file.readline().strip()
            
        #When we get to here we have processed all subtitle tracks.  This title is done.
        #current_line is either '+ title #:' or 'HandBrake has exited.'
        current_dvd.titles.append(current_title)
        
    return current_dvd
    

if __name__ == '__main__':
    g=parseDVD('/mnt/cluster-programs/handbrake/jobs/SKYLINE.iso')
    print(g)
