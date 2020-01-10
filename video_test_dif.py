from moviepy.editor import *
from PIL import Image
import os
from matplotlib import pyplot as plt
import numpy as np
from scipy.ndimage import gaussian_filter

path = r'C:\Users\Simon\Dropbox\Ableton\Underworld_v1\underworld Project\Video'
clipfile = os.path.join(path,'guitar_raw.mp4')
clip = VideoFileClip(clipfile)
im0 = clip.get_frame(0)
im0 = np.mean(im0,axis=2)
im1 = clip.get_frame(200)
im1 = np.mean(im1,axis=2)
dims = im0.shape[0:2]
dif = np.abs(im1 - im0)
print(im0.shape)

mask = (dif > 20) * 255
mask = gaussian_filter(mask, sigma=50)
mask = (mask > 40) * 255
mask = gaussian_filter(mask, sigma=20)

fsz = 7
ncol = 1
dpi = 80
margin = 0.1 # (5% of the width/height of the figure...)
figsize = (1 + margin) * dims[0] / dpi, (1 + margin) * dims[1] / dpi
fig = plt.figure(figsize=figsize, dpi=dpi)
ax = fig.add_subplot(1, 1, 1)
imax = ax.imshow(mask)
plt.show()

import pdb
pdb.set_trace()