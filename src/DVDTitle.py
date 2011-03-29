import subprocess
import re
import datetime
import time
import pickle
import os.path
from process_monitor import ProcessMonitor
from messagewriter import MessageWriter


QUALITY_FACTOR="18"

class VideoTitle(object):
    """Holds basic information about a video title to encode"""
    def __init__(self, title_number='0', main_feature='0', duration='0', number_of_tracks='0', audio_tracks={}):
        self.title_number=title_number
        self.main_feature=main_feature
        self.duration=duration
        self.number_of_tracks=number_of_tracks
        self.audio_tracks=audio_tracks
        
    def __str__(self):
        formatted="Title Number: " + str(self.title_number) + "\nDuration: " + str(self.duration) + "\nNumber of Audio Tracks: "\
       + str(self.number_of_tracks) + "\n"
        for key, value in self.audio_tracks.items():
            formatted=formatted + str(value) + "\n"
        return formatted
        
class AudioTrack(object):
    """Holds basic information about an audio track associated with a particular video title"""
    def __init__(self, track_number, track_lang, track_codec, track_channels):
        self.track_number=track_number
        self.track_lang=track_lang
        self.track_codec=track_codec
        self.track_channels=track_channels
        
    def __str__(self):        
        formatted="Track Number: " + str(self.track_number) + "\nTrack Language: " + self.track_lang + \
        "\nTrack Codec: " + self.track_codec + "\nTrack Channels: " + self.track_channels + "\n"
        return formatted
        
    
class DVD(object):
    """Stores all the information about a dvd"""
    lines_to_keep=[" title "," Main Feature","duration:","audio tracks"," ch)", "Using ", "Dolby Surround", "00Hz"]
    def __init__(self, name, disk_path):
        self.name=name
        self.disk_path=disk_path
        self.parsed_output=[]
        
    def scan_disk(self):
        '''Calls Handrake to get disk information, parse it, and come up with '''
        p = subprocess.Popen( ['HandBrakeCLI','-i',self.disk_path,'-t','0'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = p.communicate()[0].splitlines()
        for x in range(len(output)):
            output[x]=output[x].strip()
            
        output_filtered=[]
        for item in output:
            if self._keep_line(item,self.lines_to_keep) != 0:
                output_filtered.append(item)
            
        self._parse_output(output_filtered)
        
        return
            
    def _keep_line(self, query_string, search_list):
        '''Determines in a line in Handbrake's output is of interest to us'''
        if len(query_string)== 0:
            return 0
        elif query_string[0] != "+":
            return 0
        for x in search_list:
            if query_string.find(x) != -1:
                return 1
        return 0
    
    def _parse_output(self, filtered_output):
        '''Takes the raw output from a Handbrake scan and breaks it apart into strings
        representing individual titles and then sends these on for further processing
        These, in turn, are stored in the list parsed_output'''
        titles=[]
        title_lines=[]
        
        for i,str in enumerate(filtered_output):
            if str.find("title")!=-1:
                title_lines.append(i)
        if len(title_lines)==1:
            titles[0]=filtered_output
        else:
            for i,line_num in enumerate(title_lines):
                if i==(len(title_lines)-1):
                    titles.append(filtered_output[line_num:])
                else:
                    titles.append(filtered_output[line_num:title_lines[i+1]])

        for i,title in enumerate(titles):
            self.parsed_output.append(self._parse_title(title))
            
        return

    def _parse_title(self,  title_text):
        '''Takes a raw string of text from the Handbrake output (filtered per title)
        and returns a title dictionary'''
        m=re.search('([1-9][0-9]*)',title_text[0])
        currentTitle=VideoTitle(title_number=m.group(1), audio_tracks={})
        if title_text[1].find("Main Feature")!=-1:
            currentTitle.main_feature=1
            m=re.search('([0-9][0-9:]*)',title_text[2])
            n=re.search('([0-9][0-9]):([0-9][0-9]):([0-9][0-9])',m.group(1))
            currentTitle.duration=datetime.timedelta(hours=int(n.group(1)),minutes=int(n.group(2)),seconds=int(n.group(3)))
            audio_tracks_begin=4
        else:
            currentTitle.main_feature=0
            m=re.search('([0-9][0-9:]*)',title_text[1])
            n=re.search('([0-9][0-9]):([0-9][0-9]):([0-9][0-9])',m.group(1))
            currentTitle.duration=datetime.timedelta(hours=int(n.group(1)),minutes=int(n.group(2)),seconds=int(n.group(3)))
            audio_tracks_begin=3

        num_audio_tracks=len(title_text)-audio_tracks_begin

        if audio_tracks_begin < len(title_text):
            for index,i in enumerate(range(audio_tracks_begin,len(title_text))):
                currentTitle.audio_tracks ["track_"+str(index+1)]=self._parse_audio_line(title_text[i])
                currentTitle.number_of_tracks=index+1

        return currentTitle
        
    def _parse_audio_line(self,  line):
        '''Takes a line of text from the Handbrake output that describes an audio channel
        and returns a dictionary of the parsed output'''
        m = re.match('\+ ([0-9][0-9]*), ([A-Za-z][A-Za-z]*) \(([-a-zA-Z0-9]*)\) \(([a-zA-Z0-9. ]*)\)',line)
        track=AudioTrack(track_number=m.group(1),track_lang=m.group(2),track_codec=m.group(3),track_channels=m.group(4))
        return track
        
    def print_parsed_output(self):
        for i in self.parsed_output:
            print i

    
    



class EncodeCommands(object):
    '''Given a DVD's parsed output, will come up with a list of HandBrakeCLI commands'''
    def __init__(self, DVD_parsed, filename):
        self._DVD_parsed=DVD_parsed
        self._titles_to_encode=[]
        self._determine_titles_to_encode()
        self.command_lines=[]
        self._filename=filename
        for i in self._titles_to_encode:
            self._construct_handbrake_command(i, self._filename)
        
    def _determine_titles_to_encode(self):
        title_durations=[]
        for index,title in enumerate(self._DVD_parsed):
            if title.duration>datetime.timedelta(minutes=15):
                title_durations.append((title.duration,index))
                if title.duration>datetime.timedelta(hours=1,minutes=15):
                    self._titles_to_encode.append(title)
                    title_durations.pop()	#No reason to look over this during checks for episodes
        #Now we have a list of all titles that are greater than 15min long
        #and have added to our list of titles to encode any longer than 75min
        if len(title_durations)<=1:		#If there are one or fewer tracks over 15 min but under 75
            return 	#we certainly aren't dealing with a bunch of episodes
        
        title_durations=sorted(title_durations, key=lambda x:x[0])	#sort our keys by duration
        title_durations_copy=title_durations	#Ugg

        for index,i in enumerate(title_durations_copy[:-1]):	#This should get rid of all the shorter
            for j in title_durations_copy[index:]:			#documentary/interview segments
                if j[0]-i[0]>datetime.timedelta(seconds=45) and ([y[1] for y in title_durations].index(i[1])==0):	
                    title_durations.remove(i)	#so a 15,15,30 won't delete second 15
                    break
        if len(title_durations)<=1:
            return
            
        if title_durations[len(title_durations)-1][0]-title_durations[len(title_durations)-2][0]>datetime.timedelta(seconds=45):
            title_durations.pop()	#This covered the case of 15,15,30, am not checking for multiples
            
        if len(self._titles_to_encode)>0:	#This checks if a long title is all the episodes put together
            if datetime.timedelta(seconds=-45)<self._titles_to_encode[0].duration-title_durations[0][0]*len(title_durations)<datetime.timedelta(seconds=45):
                del self._titles_to_encode[0]
                
        
        for i in title_durations:
            self._titles_to_encode.append(self._DVD_parsed[i[1]])
        
        
        return
        
    #This takes a title dictionary, the path to the file and the filename, sans ext 
    #and returns a completed command line for Handbrake
    def _construct_handbrake_command(self, title, filename):
        num_tracks=title.number_of_tracks
        audio_string=""
        codec_string=""
        audio_language=""
        for i in range(num_tracks):
            track=title.audio_tracks.get('track_'+str(i+1))
            if track.track_lang == "English" or track.track_lang=="Unknown":
                a, b, c=self._construct_audio_compression(track)
                audio_string += a
                codec_string += b
                audio_language += c

        audio_string=audio_string[:-1]	#remove trailing comma
        codec_string=codec_string[:-1]
        audio_language=audio_language[:-1]
        self.command_lines.append(['HandBrakeCLI','-i',filename,'-t',title.title_number,'-o',filename + '_title_'+title.title_number+'.mkv','-f','mkv','-m','-e','x264','-q', QUALITY_FACTOR, '-x', 'ref=2:bframes=2:subq=6:mixed-refs=0:weightb=0:8x8dct=0:trellis=0', '--strict-anamorphic','-a',audio_string,'-E',codec_string,'-6','-A', audio_language])

        return

    #Takes a track dictionary and returns three strings, the arguments for
    #-a, -E and -A.  Note that it appends a comma to the end of the string
    #this must be removed if it is the last argument
    def _construct_audio_compression(self, track):
        audio_string=track.track_number+","
        audio_language=track.track_lang+","
        if track.track_codec=="AC3" or track.track_codec=="Dolby Surround":
            codec_string="copy:ac3,"
        elif track.track_codec=="DTS":
            codec_string="copy:dts,"
        else:
            codec_string="faac,"
        return audio_string,codec_string,audio_language


def ProcessDVD(path,preset='Archival'):
    (base_dir,file_name)=os.path.split(path)
    (root,)=os.path.splitext(file_name)
    os.chdir(base_dir)
    os.mkdir(root)
    subprocess.check_call(['mount','-t','loop',file_name,root])
    cur_disk=DVD(root,path)
    cur_disk.scan_disk()
    commands=EncodeCommands(cur_disk.parsed_output,root)
    subprocess.check_call(['umount',root])
    writer=MessageWriter(server='Chiana', vhost='cluster-programs', \
                         userid='cluster-admin', password='1234', \
                         exchange='handbrake', exchange_durable=True, \
                         exchange_auto_delete=False, exchange_type='direct',\
                         routing_key='job-queue', queue_durable=True,\
                         queue_auto_delete=False)
    for i,item in enumerate(commands):
        os.mkdir(root+'job'+str(i))
        subprocess.check_call(['mount','-t','loop',file_name,root+'job'+str(i)])
        writer.send_message(pickle.dumps([base_dir+root+'job'+str(i),item]))
        
    



if __name__ == '__main__':
    filename_no_ext='bsg4-3'
    filename='bsg4-3.iso'
    dvd=DVD('bsg4-3', 'bsg4-3.iso')
    dvd.scan_disk()
    
    commands=EncodeCommands(dvd.parsed_output, filename_no_ext)
