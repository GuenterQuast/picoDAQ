# -*- coding: utf-8 -*-

'''effective Voltage and signal history in TKinter window'''

from __future__ import print_function, division, unicode_literals
from __future__ import absolute_import

import sys, time, numpy as np

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
    interval = WaitTime/1000.  # in ms 
    cnt = 0
    dTcum = 0.
    tStart = time.time()
    try:
      while True:
        data = Q.get()
        if data == None:
          #print('*==* yieldEvt_fromQ: received end event')          
          sys.exit()
        cnt+=1
        yield (cnt,) + data
# guarantee correct timing 
        deltaTime = time.time() - tStart
        dtcor = interval - deltaTime + dTcum
        if dtcor > 0. : time.sleep(dtcor) 
        dTcum += interval
    except:
      #print('*==* yieldEvt_fromQ: termination signal received')
      sys.exit()

# ------- executable part -------- 
#  print(' -> mpVMeter starting')

  VM = VoltMeter(conf)
  figVM = VM.fig

# generate a simple window for graphics display as a tk.DrawingArea
  root = Tk.Tk()
  root.wm_title("Voltmeter Display")
  canvas = FigureCanvasTkAgg(figVM, master=root)
  canvas.draw()
  canvas.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)
  canvas._tkcanvas.pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)
  button = Tk.Button(master=root, text='Quit', command=sys.exit)
  button.pack(side=Tk.BOTTOM)

# set up matplotlib animation
  VMAnim = anim.FuncAnimation(figVM, VM, yieldEvt_fromQ,
                         interval = 1., init_func = VM.init,
                         blit=True, fargs=None, repeat=True, save_count=None)
                       # save_count=None is a (temporary) work-around 
                       #     to fix memory leak in animate
  try:
    Tk.mainloop()
   
  except:
    print('*==* mpVMeter: termination signal recieved')
  sys.exit()
