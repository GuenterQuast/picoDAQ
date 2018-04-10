# -*- coding: utf-8 -*-

'''Oscilloscope display in TKinter window'''

from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import sys, numpy as np

import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
if sys.version_info[0] < 3:
  import Tkinter as Tk
else:
  import tkinter as Tk
import matplotlib.pyplot as plt, matplotlib.animation as anim

# import Oscilloscope class
from .Oscilloscope import *

def mpOsci(Q, conf, interval = 50., name='event rate'):
  '''Oscilloscpe display of data passed via multiprocessing.Queue
    Args:
      conf: picoConfig object
      Q:    multiprocessing.Queue()   
  '''

  # Generator to provide data to animation
  def yieldEvt_fromQ():
# random consumer of Buffer Manager, receives an event copy 
   # via a Queue from package mutiprocessing
   
    cnt = 0
    try:
      while True:
        evNr, evTime, evData = Q.get()
        #print('*==* yieldEvt_fromQ: received event %i' % evNr)
        cnt+=1
        evt = (cnt, evNr, evTime, evData)
        yield evt
    except:
      print('*==* yieldEvt_fromQ: termination signal received')
  
# ------- executable part -------- 
#  print(' -> mpOsci starting')

  try:

    Osci = Oscilloscope(conf, name)
    figOs = Osci.fig

# generate a simple window for graphics display as a tk.DrawingArea
    root = Tk.Tk()
    root.wm_title("Oscilloscope Display")
    canvas = FigureCanvasTkAgg(figOs, master=root)
    canvas.draw()
    canvas.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)
    canvas._tkcanvas.pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)
    button = Tk.Button(master=root, text='Quit', command=sys.exit)
    button.pack(side=Tk.BOTTOM)

# set up matplotlib animation
    osciAnim = anim.FuncAnimation(figOs, Osci, yieldEvt_fromQ, 
                  init_func=Osci.init, interval=interval, blit=True,
                  fargs=None, repeat=True, save_count=None)
                       # save_count=None is a (temporary) work-around 
                       #     to fix memory leak in animate
    Tk.mainloop()
   
  except:
    print('*==* mpOsci: termination signal recieved')
  sys.exit()
