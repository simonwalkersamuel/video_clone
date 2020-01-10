# -*- coding: utf-8 -*-
"""
Created on Wed Oct 09 13:52:08 2019

@author: simon
"""

from __future__ import print_function

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import os
import nibabel as nib
from matplotlib.widgets import Slider, Button, RadioButtons, TextBox
from PIL import Image, ImageDraw
from scipy import ndimage
import scipy.signal
import pickle
from tkinter.filedialog import askopenfilename, asksaveasfilename
from scipy.ndimage import gaussian_filter
from moviepy.editor import *
import cv2

class VideoSeg():

    def __init__(self,path,file,restrict=10):
        
        # Initialise some variables
        self.segax = None
        self.seg_ind = 0
        self.nseg = 10
        self.points = [None]*self.nseg # save
        
        # Session data
        self.path = path # Main directory
        self.file = file
    
        # Load data
        #from os import listdir
        #from os.path import isfile, join
        #self.files = [f for f in listdir(path) if isfile(join(path, f))]
        #if restrict is not None:
        #    self.files = self.files[0:restrict]
        self.clip = VideoFileClip(os.path.join(self.path,self.file))
        
        # Get image dimensions
        self.dims = self.clip.size
        self.nframes = np.floor(self.clip.duration*self.clip.fps).astype('int')
        #im0 = self.load_image(self.files[0])
        #self.dims = (len(self.files),)+im0.shape
        #print('Data size: {}'.format(self.dims))
        #self.images = np.zeros(self.dims,dtype=im0.dtype)
        self.mask = None
        
        # Load images
        #for i,file in enumerate(self.files):
        #    try:
        #        self.images[i,:,:,:] = self.load_image(file)
        #    except Exception as e:
        #        print('Could not load {}. Error: {}'.format(file,e))
        
        self.ind = 0

        ### CREATE GUI ###
        fsz = 7
        ncol = 1
        dpi = 80
        margin = 0.1 # (5% of the width/height of the figure...)
        figsize = (1 + margin) * self.dims[0] / dpi, (1 + margin) * self.dims[1] / dpi
        self.fig = plt.figure(figsize=figsize, dpi=dpi) #figsize=(fsz*ncol,fsz))
        self.ax = self.fig.add_subplot(1, ncol, 1)
        self.pointax = self.ax.plot([],[],'s',color='yellow',marker='x')
        
        self.create_image_plot()
        
        axcolor = 'lightgoldenrodyellow'
        self.axslice = plt.axes([0.25, 0.05, 0.5, 0.05], facecolor=axcolor)
        self.sslice = Slider(self.axslice, '', 1, self.dims[0], valinit=float(self.ind), valstep=1)
        self.sslice.on_changed(self.onsliderchange)
        
        self.shift_is_held = False
        self.ctrl_is_held = False
        self.slider_update_only = False
        
        self.update()
        
    def plot_audio(self):
        audio = self.clip.audio.to_soundarray()
        time = np.linspace(0.,self.clip.audio.duration,audio.shape[0])
        plt.plot(time,audio[:,0])
        plt.show()
        
    def set_start(self):
        pass
        
    def load_image(self,file):
        f0 = os.path.join(self.path,file)
        im0 = Image.open(f0).convert('RGBA')
        im0 = np.array(im0)
        return im0
        
    def create_image_plot(self):
        plt.sca(self.ax)
        Z1 = np.add.outer(range(8), range(8)) % 2  # chessboard
        self.bg = self.ax.imshow(Z1, cmap=plt.cm.gray, interpolation='nearest',extent=(0,self.dims[0],0,self.dims[1]))
        im = self.clip.get_frame(0) 
        self.im = self.ax.imshow(im)
        self.ax.axis('off')
        
    def onpress(self,event):
        """
        Respond to mouse button click events in the image window
        """
        if event.button==1 and event.dblclick==False and self.ctrl_is_held:
            self.add_point([int(event.xdata),int(event.ydata)])
        elif event.button==3 and event.dblclick==False and self.ctrl_is_held:
            self.complete_point_polygon()
            
    def onsliderchange(self,value):
        """
        Respond to slider value changing
        """
        if self.slider_update_only: # Avoid loop...
            self.slider_update_only = False
            return
        self.ind = int(value) - 1
        self.update()    
            
    def onkeypress(self,event):
        """
        Respond to key press events in the image window
        Buffer shift and control key presses
        """
        if event.key == 'shift':
            self.shift_is_held = True
        if event.key == 'control':
            self.ctrl_is_held = True
        if event.key == 'up':
            self.ind = int(np.clip((self.ind + 1),0,self.X.shape[1]-1))
            self.update()
        if event.key == 'down':
            self.ind = int(np.clip((self.ind - 1),0,self.X.shape[1]-1))
            self.update()
        
    def onkeyrelease(self,event):
        """
        Respond to key release events in the image window
        Buffer shift and control key presses
        """
        if event.key == 'shift':
            self.shift_is_held = False
        if event.key == 'control':
            self.ctrl_is_held = False
            
    def onmotion(self,event):
        """
        Respond to motion events in the image window
        """
        return
        # Which axis?
        if self.ax==event.inaxes: # image axis
            if event.xdata is None:
                return
            self.update_plot(event.xdata,event.ydata)   
        
    def onscroll(self, event):
        """
        Respond to scroll events in the image window
        """
        if event.button == 'up':
            self.ind = int(np.clip((self.ind + 1),0,self.dims[0]-1))
        else:
            self.ind = int(np.clip((self.ind - 1),0,self.dims[0]-1))
        self.update()
        
    def update(self):

        self.slider_update_only = True # Avoid going through endless update loops...
        self.sslice.set_val(float(self.ind+1))
        
        self.update_points()
            
        self.fig.suptitle('Image {} of {}'.format(self.ind+1,self.dims[0]), fontsize=20)
        im = self.clip.get_frame(self.ind / self.clip.fps).copy()
        #im = np.expand_dims(im, axis=-1) # add alpha channel
        im = cv2.cvtColor(im, cv2.COLOR_RGB2RGBA) # convert to RGBA
        #im = self.images[self.ind,:,:,:]
        print('Image min/max: {},{}'.format(np.min(im),np.max(im)))
        if self.mask is not None:
            print('Mask min/max: {},{}'.format(np.min(self.mask),np.max(self.mask)))
            #mask_blur = mask_blur * 255 / np.max(mask_blur)
            im[:,:,-1] = self.mask_blur
        self.im.set_data(im)
        self.im.axes.figure.canvas.draw()
            
        self.fig.canvas.draw()
        
    def add_point(self,coords):
        if len(self.pointax)==0:
            self.pointax = self.ax.plot(coords[0],coords[1],'s',color='yellow',marker='x')

        print('ADDED POINT: {}'.format(coords))

        if self.points[self.seg_ind]==None:
            self.points[self.seg_ind] = {'coords':[coords],'complete':False}
            #self.points[self.seg_ind]['coords'] = [coords]
        else:
            # Just append
            self.points[self.seg_ind]['coords'].append(coords)
        self.update_points()
        self.fig.canvas.draw() 
        
    def complete_point_polygon(self):
        if self.points[self.seg_ind]==None or self.points[self.seg_ind]['complete']==True or len(self.points[self.seg_ind]['coords'])<=1:
            return

        c0 = self.points[self.seg_ind]['coords'][0]
        self.add_point(c0)
        self.points[self.seg_ind]['complete'] = True
        
        polygon = [(x[0],x[1]) for x in self.points[self.seg_ind]['coords']]
        
        img = Image.new('L', (self.dims[0], self.dims[1]), 0)
        ImageDraw.Draw(img).polygon(polygon, outline=255, fill=255)
        self.mask = np.array(img)
        self.mask_blur = gaussian_filter(self.mask, sigma=15)
        
        print('COMPLETED ROI: {}'.format(polygon))
        self.update()
        
        file,info = self.pickfile()
        if file!='':
            im = Image.fromarray(self.mask_blur)
            im.save(file)
        
    def pickfile(self,**kwargs):
        file = asksaveasfilename(**kwargs)
        if file=='':
            return None,None
        absfile = os.path.abspath(file)
        dir,basename = os.path.dirname(absfile),os.path.basename(absfile)
        _,ext = os.path.splitext(basename)
        return absfile,[dir,basename,ext]
        
    def update_points(self):

        """
        Update plotting of points
        """
        
        i = self.seg_ind

        if self.points[i]!=None:
            points = self.points[i]['coords']
            xf = np.asarray(self.points[i]['coords'])
            if len(xf)>0:
                x,y = xf[:,0],xf[:,1]
                self.pointax[0].set_data(x,y)
            else:
                self.pointax[0].set_data([],[])
        elif self.pointax is not None and len(self.pointax)>0:
            self.pointax[0].set_data([],[])

    def get_file_list(self):
        return [f for f in os.listdir(self.path) if os.path.isfile(os.path.join(self.path,f)) and '.nii' in f]

def main():

    #path = r'C:\Users\simon\Dropbox\Personal\Music\clone_trial\FrameGrab\bass'
    #path = r'C:\Users\Simon\Dropbox\Personal\Music\clone_trial'
    path = r'C:\Users\Simon\Dropbox\Ableton\Underworld_v1\underworld Project\Video'
    file = os.path.join(path,'bass_raw.mp4')

    rseg = VideoSeg(path,file)
    
    rseg.fig.canvas.mpl_connect('button_press_event', rseg.onpress)
    rseg.fig.canvas.mpl_connect('scroll_event', rseg.onscroll)
    rseg.fig.canvas.mpl_connect('motion_notify_event', rseg.onmotion)
    rseg.fig.canvas.mpl_connect('key_press_event', rseg.onkeypress)
    rseg.fig.canvas.mpl_connect('key_release_event', rseg.onkeyrelease)

    plt.show()

if __name__ == "__main__":
    main()