# -*- coding: utf-8 -*-

'''Effective Voltage in TKinter window'''

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

# import Voltmeter class
from .VoltMeter import *

def mpVMeter(Q, conf, WaitTime=500., name='effective Voltage'):
  '''effective Voltage of data passed via multiprocessing.Queue
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
#  print(' -> mpVMeter starting')

  VM = VoltMeter(conf)
  figVM = VM.fig

# generate a simple window for graphics display as a tk.DrawingArea
  root = Tk.Tk()
  root.wm_title("Voltmeter Display")
  canvas = FigureCanvasTkAgg(figVM, master=root)
  canvas.show()
  canvas.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)
  canvas._tkcanvas.pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)
  button = Tk.Button(master=root, text='Quit', command=sys.exit)
  button.pack(side=Tk.BOTTOM)

# set up matplotlib animation
  VMAnim = anim.FuncAnimation(figVM, VM, yieldEvt_fromQ,
                         interval=WaitTime, init_func=VM.init,
                         blit=True, fargs=None, repeat=True, save_count=None)
                       # save_count=None is a (temporary) work-around 
                       #     to fix memory leak in animate
  try:
    Tk.mainloop()
   
  except:
    print('*==* mpVMeter: termination signal recieved')
  sys.exit()
