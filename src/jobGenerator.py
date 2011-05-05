import datetime
import os.path

class jobTemplate(object):
    def __init__(self):
        self.min_length=datetime.timedelta(seconds=0)
        self.max_length=datetime.timedelta(hours=10)
        self.preset=None
        self.anamorphic='--strict-anamorphic'
        self.quality_factor=18
        self.audio_to_keep=dict([['track_nums',[1]], ['track_lang',['English','Unknown']]])
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
            
if __name__ == '__main__':
    import pprint
    from newparser import * #@UnusedWildImport
    g=pickle.load(open('bsg-dump','r'))
    commands=jobGenerator(g,Movie())
    pp=pprint.PrettyPrinter(indent=4)
    pp.pprint(commands)
            
            