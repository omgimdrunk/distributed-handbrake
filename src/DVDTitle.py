import subprocess
import re
import datetime
import pickle
import os.path
from messagewriter import MessageWriter
import logging
import threading
import sys
from config import *


logging.basicConfig(level=logging.ERROR)

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
    def __init__(self, disk_path):
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

        #num_audio_tracks=len(title_text)-audio_tracks_begin

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
    def __init__(self, DVD_parsed, filename_no_ext, quality, preset='Archival'):
        self._DVD_parsed=DVD_parsed
        self._titles_to_encode=[]
        self.command_lines=[]
        self._filename=filename_no_ext
        self._quality=quality
        self._preset=preset
        #Presets are currently not implemented        
        
        logging.debug('Determining titles to encode')
        self._determine_titles_to_encode()
        logging.debug('Creating HandBrake commands')
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
        self.command_lines.append(['HandBrakeCLI','-t',title.title_number,'-o',filename + '_title_'+title.title_number+'.mkv','-f','mkv','-m','-e','x264','-q', self._quality, '-x', 'ref=2:bframes=2:subq=6:mixed-refs=0:weightb=0:8x8dct=0:trellis=0', '--strict-anamorphic','-a',audio_string,'-E',codec_string,'-6','-A', audio_language])

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


class ProcessDVD(threading.Thread):
    '''Accepts a path to a new video file to process and outputs a set of
    Handbrake Encode Commands to a RabbitMQ server.
    
    path is the full path to the new video file
    file_name is the file name with extension
    root is the file name with no extension
    
    If the video file is a single file (handle mkv, avi, or mp4) will simply pass
    it off to Handbrake in the form tuple(file_name,[Encode Command])
    
    If the video file is an ISO will mount the ISO, decide on which titles to encode,
    create a set of directories of the form root_job_#num and mounts the ISO on them.
    Finally emits a string of encode commands in the form tuple(root,[Encode Command])'''
    
    def __init__(self,path):
        '''All we have to do here is start up the Threading interface and save the path'''
        
        threading.Thread.__init__(self)
        self.path=path
        
    def run(self):
        '''Main body of the code.'''
        
        logging.debug('ProcessDVD called with argument ' + self.path)
        (base_dir,file_name)=os.path.split(self.path)
        (root,ext)=os.path.splitext(file_name)
        logging.debug('Changing directory to ' + base_dir)
        os.chdir(base_dir)
        if ext == '.ISO' or '.iso':
            logging.debug('ISO file detected, proceding to mount')
            logging.debug('Making directory ' + root)
            try:
                os.mkdir(root)
            except OSError:
                logging.debug('Directory exists, using existing')
                if len(os.listdir(root)) != 0:
                    logging.debug('It appears something is mounted at '+root)
                    logging.debug('Attempting unmount')
                    try:
                        subprocess.check_call(['sudo','umount',root])
                    except:
                        logging.debug('Unmount failed')
                        sys.exit('Mountpoint exists and has contents')
                
            logging.debug('Mounting iso '+file_name+' to '+root)
            try:
                subprocess.check_call(['sudo','mount','-o','loop',file_name,root])
            except:
                sys.exit('An unhandled exception occurred while executing a mount command. \
                Check that you have passwordless sudo mount enabled')
            self.cur_disk=DVD(os.path.join(base_dir,root))          
        elif ext == '.mp4' or '.MP4' or '.mkv' or '.MKV' or '.avi' or '.AVI':
            logging.debug('Non-ISO video file detected')
            self.cur_disk=DVD(self.path)
        else:
            logging.error('Only ISOs, MP4s, MKVs, and AVIs are handled')
            sys.exit('Only ISOs, MP4s, MKVs, and AVIs are handled')
            
        logging.debug('Scanning video')
        self.cur_disk.scan_disk()
        logging.debug('Generating encoding commands')
        commands=EncodeCommands(DVD_parsed=self.cur_disk.parsed_output,filename_no_ext=root,quality='18')

        if ext == '.ISO' or '.iso':
            logging.debug('Unmounting ISO')
            try:
                subprocess.check_call(['sudo','umount',root])
            except:
                logging.error('Unmounting failed.  Ensure that passworless sudo umount\
                is enabled')  
            logging.debug('Removing temporary mount directory')
            try:
                os.rmdir(root)
            except:
                logging.error('Unable to remove temporary mount directory '+root)
                
        logging.debug('Establishing connection with message server')
        writer=MessageWriter(server=MESSAGE_SERVER, vhost=VHOST, \
                         userid=MESSAGE_USERID, password=MESSAGE_PWD, \
                         exchange=EXCHANGE, exchange_durable=True, \
                         exchange_auto_delete=False, exchange_type='direct',\
                         routing_key=JOB_QUEUE, queue_durable=True,\
                         queue_auto_delete=False)
        
        for i,command in enumerate(commands.command_lines):
            job_mountpoint=''
            if ext == '.ISO' or '.iso':
                #Must mount an ISO, will leave mounted until job complete message
                job_mountpoint=root+'_job_'+str(i)
                logging.debug('Making job subdirectory ' + job_mountpoint)
                try:
                    os.mkdir(job_mountpoint)
                except OSError:
                    logging.debug('Directory already exists, assuming previous mount')
                    if len(os.listdir(job_mountpoint)) != 0:
                        try:
                            subprocess.check_call(['sudo','umount',job_mountpoint])
                        except:
                            logging.error('Unable to unmount ' + job_mountpoint +'. Skipping')
                            continue
                logging.debug('Mounting ISO at ' + job_mountpoint)
                try:
                    subprocess.check_call(['sudo','mount','-o','loop',file_name,job_mountpoint])
                except:
                    logging.error('Unhandled exception while mounting ISO for job.\
                     Check that passworless sudo mount is available.')
                    logging.error('Skipping')
                    continue
            else:
                job_mountpoint=file_name
            
            logging.debug('Appending output file to command')
            command.append('-i')
            command.append(job_mountpoint)
            logging.debug('Sending complete command to message server')
            writer.send_message(pickle.dumps([os.path.join(base_dir,job_mountpoint),command]))
        
    



if __name__ == '__main__':
    ProcessDVD('/mnt/cluster-programs/handbrake/jobs/CHARLIE_WILSONS_WAR.ISO').run()
