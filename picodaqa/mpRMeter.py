# -*- coding: utf-8 -*-

'''Rate history display in TKinter window'''

from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import sys, time, numpy as np

import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
if sys.version_info[0] < 3:
  import Tkinter as Tk
else:
  import tkinter as Tk
import numpy as np, matplotlib.pyplot as plt, matplotlib.animation as anim

# import RMeter class
from .RMeter import *

def mpRMeter(Q, maxRate = 10. , interval = 2500.):
  '''RateMeter: show rate history
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
      print('*==* yieldEvt_fromQ: termination signal recieved')
  
# ------- executable part -------- 
  print(' -> mpRMeter starting')

  try:
    RM = RMeter(maxRate, interval)
    figRM = RM.fig

# generate a simple window for graphics display as a tk.DrawingArea
    root = Tk.Tk()
    root.wm_title("Rate Display")
    canvas = FigureCanvasTkAgg(figRM, master=root)
    canvas.show()
    canvas.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)
    canvas._tkcanvas.pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)
    button = Tk.Button(master=root, text='Quit', command=sys.exit)
    button.pack(side=Tk.BOTTOM)

# set up matplotlib animation
    RMAnim = anim.FuncAnimation(figRM, RM, yieldEvt_fromQ, 
                        init_func=RM.init, interval=interval, blit=True,
                        fargs=None, repeat=True, save_count=None)
                             # save_count=None is a (temporary) work-around 
                             #     to fix memory leak in animate
    Tk.mainloop()
   
  except:
    print('*==* mpRMeter: termination signal recieved')
  sys.exit()
