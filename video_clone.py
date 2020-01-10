from moviepy.editor import *
from PIL import Image
import os

path = r'C:\Users\Simon\Dropbox\Ableton\Underworld_v1\underworld Project\Video'
bass_clip_file = os.path.join(path,'bass_raw.mp4')
guitar_clip_file = os.path.join(path,'guitar_raw.mp4')
drum_clip_file = os.path.join(path,'drums_raw2.mp4')

audioclip = AudioFileClip(os.path.join(path,'underworld.wav'))
bpm = 135.
bar_duration = 4.*60./bpm
intro_duration = bar_duration * 2
audioclip = audioclip.set_start(intro_duration)

bass_clip = VideoFileClip(bass_clip_file)
guitar_clip = VideoFileClip(guitar_clip_file)
drum_clip = VideoFileClip(drum_clip_file)

def normalise(image):
    return image/255.

# Set position offsets and start points
#drum_clip = drum_clip.set_pos((0,-25))
drum_start = 34.1446 + intro_duration
guitar_start = 17.716 + intro_duration
bass_start = 13.28 + intro_duration
drum_clip = drum_clip.subclip(drum_start, drum_clip.duration)
guitar_clip = guitar_clip.subclip(guitar_start, guitar_clip.duration)
bass_clip = bass_clip.subclip(bass_start, bass_clip.duration)
#drum_clip = drum_clip.set_start(34.1446)
#guitar_clip = guitar_clip.set_start(14.20)
#bass_clip c= bass_clip.set_start(13.28)

# Masking
guitar_mask_clip = ImageClip(os.path.join(path,"guitar_mask.jpg"), ismask=True)
guitar_mask_clip = guitar_mask_clip.fl_image(normalise)
guitar_clip = guitar_clip.set_mask(guitar_mask_clip)

bass_mask_clip = ImageClip(os.path.join(path,"bass_mask.jpg"), ismask=True)
bass_mask_clip = bass_mask_clip.fl_image(normalise)
bass_clip = bass_clip.set_mask(bass_mask_clip)

final_clip = CompositeVideoClip([drum_clip,guitar_clip]) #,bass_clip])
final_clip = final_clip.set_audio(audioclip)
#final_clip = final_clip.subclip(0.,30.)
#final_clip = final_clip.set_end(65.)
#final_clip.save_frame(os.path.join(path,"frame.png"),t=60)
final_clip.write_videofile(os.path.join(path,'underworld_clone.mp4'),audio=True,fps=drum_clip.fps)
