from moviepy.editor import *
from matplotlib import pyplot as plt
import numpy as np

path = r'C:\Users\Simon\Dropbox\Ableton\Underworld_v1\underworld Project\Video'
file = os.path.join(path,'guitar_raw.mp4')

clip = VideoFileClip(file)

audio = clip.audio.to_soundarray()
time = np.linspace(0.,clip.audio.duration,audio.shape[0])
plt.plot(time,audio[:,0])
plt.show()