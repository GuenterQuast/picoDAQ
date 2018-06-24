# -*- coding: utf-8 -*-

'''Signal history in TKinter window'''

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
from .DataLogger import *


def mpDataLogger(Q, conf, WaitTime=100., name='(Veff)'):
  '''effective Voltage of data passed via multiprocessing.Queue
    Args:
      conf: picoConfig object
      Q:    multiprocessing.Queue()   
  '''

  # Generator to provide data to animation
  def yieldEvt_fromQ():
  # receives data via Queue from package mutiprocessing 
    interval = WaitTime/1000.  # in s 
    cnt = 0
    try:
      while True:
        T0 = time.time()
        evData = Q.get()
        if evData == None:
          #print('*==* yieldEvt_fromQ: received end event')          
          sys.exit()
        #print('*==* yieldEvt_fromQ: received event %i' % evNr)
        cnt+=1
        evt = (cnt, evData)
        yield evt
# guarantee correct timing 
        dtcor = interval - time.time() + T0
        if dtcor > 0. :  time.sleep(dtcor) 

    except:
      # print('*==* yieldEvt_fromQ: termination signal received')
      return
# ------- executable part -------- 
#  print(' -> mpDataLogger starting')

  DL = DataLogger(WaitTime, conf, name)
  figDL = DL.fig

# generate a simple window for graphics display as a tk.DrawingArea
  root = Tk.Tk()
  root.wm_title("Data Logger")
  canvas = FigureCanvasTkAgg(figDL, master=root)
  canvas.draw()
  canvas.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)
  canvas._tkcanvas.pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)
  button = Tk.Button(master=root, text='Quit', command=sys.exit)
  button.pack(side=Tk.BOTTOM)

# set up matplotlib animation
  VMAnim = anim.FuncAnimation(figDL, DL, yieldEvt_fromQ,
                         interval = 1. , init_func=DL.init,
                         blit=True, fargs=None, repeat=True, save_count=None)
                       # save_count=None is a (temporary) work-around 
                       #     to fix memory leak in animate
  try:
    Tk.mainloop()
   
  except:
    print('*==* mpDataLogger: termination signal recieved')
  sys.exit()
# -- end def mpDataLogger()
