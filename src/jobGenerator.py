import datetime
import os.path
import threading
from messaging import MessageWriter
import sys
import socket

from config import * #@UnusedWildImport
from newparser import * #@UnusedWildImport

class jobTemplate(object):
    def __init__(self):
        self.min_length=datetime.timedelta(seconds=0)
        self.max_length=datetime.timedelta(hours=10)
        self.preset=None
        self.anamorphic='--strict-anamorphic'
        self.quality_factor=18
        self.audio_to_keep=dict([['track_nums',['1']], ['track_lang',['English','Unknown']]])
        self.subtitles_to_keep=dict([['track_nums',[None]], ['track_lang','English']])
        self.audio_conversion=dict([['copy','All'], ['bitrate','160'], ['fallback','lame']])
        self.output_type='.mkv'
        self.x264_options='ref=2:bframes=2:subq=6:mixed-refs=0:weightb=0:8x8dct=0:trellis=0'
        
class TVShow(jobTemplate):
    def __init__(self):
        jobTemplate.__init__(self)
        self.min_length=datetime.timedelta(minutes=35)
        self.max_length=datetime.timedelta(minutes=55)
        
class Movie(jobTemplate):
    def __init__(self):
        jobTemplate.__init__(self)
        self.min_length=datetime.timedelta(hours=1)

def HBCombine(base_string,addition):
    if base_string == '':
        return addition
    else:
        return base_string+','+addition
        
def jobGenerator(current_dvd, job_template):
    encode_commands=[]
    (_,input_name)=os.path.split(current_dvd.name)
    
    for title in current_dvd.titles:
        audio_tracks_to_convert=''
        audio_track_names=''
        audio_conversions=''
        audio_bitrate=''
        subtitle_tracks_to_copy=''
        subtitle_tracks_names=''
        
        if title.duration>job_template.min_length and title.duration<job_template.max_length:

            for audio_track in title.audio_tracks:
                if audio_track.language in job_template.audio_to_keep.get('track_lang') or \
                audio_track.track_number in job_template.audio_to_keep.get('track_nums'):
                    audio_tracks_to_convert=HBCombine(audio_tracks_to_convert,audio_track.track_number)
                        
                    if audio_track.track_number in job_template.audio_conversion.get('copy') \
                    or job_template.audio_conversion.get('copy') == 'All':
                        audio_conversions=HBCombine(audio_conversions,'copy')
                        audio_bitrate=HBCombine(audio_bitrate,job_template.audio_conversion.get('bitrate'))
                            
                    else:
                        audio_conversions=HBCombine(audio_conversions,job_template.audio_conversion.get('fallback'))
                        audio_bitrate=HBCombine(audio_bitrate,job_template.audio_conversion.get('bitrate'))
                    audio_track_names=HBCombine(audio_track_names,audio_track.language)
                    
            for subtitle in title.subtitles:
                if subtitle.track_number in job_template.subtitles_to_keep.get('track_nums') or \
                subtitle.language in job_template.subtitles_to_keep.get('track_lang'):
                    subtitle_tracks_to_copy=HBCombine(subtitle_tracks_to_copy,subtitle.track_number)
                    subtitle_tracks_names=HBCombine(subtitle_tracks_names,subtitle.language_code)
            
            if job_template.preset == None:        
                encode_commands.append(['HandBrakeCLI','-i',input_name,'-o',current_dvd.title+'_track_'+\
                        title.title_number+job_template.output_type,'-m','-e','x264',\
                        '-q', job_template.quality_factor, '-x', job_template.x264_options, \
                        job_template.anamorphic,'-a', audio_tracks_to_convert, '-B', audio_bitrate, \
                        '-A', audio_track_names, '-s', subtitle_tracks_to_copy, '--srt-lang', \
                        subtitle_tracks_names, '-E', audio_conversions])
            else:
                encode_commands.append(['HandBrakeCLI','-i',input_name,'-o',current_dvd.title+'_track_'+\
                        title.title_number+job_template.output_type,'-m', '-Z',job_template.preset,\
                        '-a', audio_tracks_to_convert,'-B', audio_bitrate, '-A', audio_track_names,\
                        '-s', subtitle_tracks_to_copy, '--srt-lang', subtitle_tracks_names])
    
    return encode_commands
            
            
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
        if ext == '.ISO' or ext == '.iso':
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
            self.cur_disk_path=os.path.join(base_dir,root)         
        elif ext == '.mp4' or ext == '.MP4' or ext == '.mkv' or ext == '.MKV' \
        or ext == '.avi' or ext == '.AVI' or ext == '.mts' or ext == '.MTS':
            logging.debug('Non-ISO video file detected')
            self.cur_disk_path=self.path
        else:
            logging.error('Only ISOs, MP4s, MKVs, MTSs, and AVIs are handled')
            sys.exit('Only ISOs, MP4s, MKVs, MTSs, and AVIs are handled')
            
        logging.debug('Scanning video')
        parsed_DVD=parseDVD(self.cur_disk_path)
        logging.debug('Generating encoding commands')
        commands=jobGenerator(parsed_DVD,Movie())

        if ext == '.ISO' or ext == '.iso':
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
        
        for i,command in enumerate(commands):
            job_mountpoint=''
            if ext == '.ISO' or ext == '.iso':
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
            myip=socket.gethostbyname(socket.getfqdn())
            ftp_location='ftp://' + str(myip) + ':' + str(FTP_PORT) + '/jobs/' + job_mountpoint
            writer.send_message(pickle.dumps([job_mountpoint,ftp_location,command]))
            
        writer.close()            


if __name__ == '__main__':
    import pprint
    from newparser import * #@UnusedWildImport
    g=pickle.load(open('bsg-dump','r'))
    commands=jobGenerator(g,Movie())
    pp=pprint.PrettyPrinter(indent=4)
    pp.pprint(commands)
            
            
