# -*- coding: utf-8 -*-

'''Bargraph Display in in TKinter window'''

from __future__ import print_function, division, unicode_literals
from __future__ import absolute_import

import sys, numpy as np, time

import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
if sys.version_info[0] < 3:
  import Tkinter as Tk
else:
  import tkinter as Tk
import matplotlib.pyplot as plt, matplotlib.animation as anim

# import Voltmeter class
from .BarDisplay import *

def mpBDisplay(Q, conf, mode=0, size=1, name='SignalSize'):
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
        while not Q.qsize(): 
          time.sleep(0.1)
        vals = Q.get()
        cnt+=1
        yield vals
    except:
      print('*==* yieldData_fromQ: termination signal received')
      return

  def yield_test(): 
    try:
      while True:
        time.sleep(np.random.rand())
        vals = np.random.rand(3)
        yield vals
    except:
      print('*==* yield_test: termination signal received')
      return

             
# ------- executable part -------- 
#  print(' -> mpBDisplay starting')

  try:
    while True:
      BD = BarDisplay(conf, mode, size)
      figBD = BD.fig
#      print(' -> PanelMeter initialized')

# generate a simple window for graphics display as a tk.DrawingArea
      root = Tk.Tk()
      root.wm_title(name)
      canvas = FigureCanvasTkAgg(figBD, master=root)
      canvas.draw()
      canvas.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)
      canvas._tkcanvas.pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)
      button = Tk.Button(master=root, text='Quit', command=sys.exit)
      button.pack(side=Tk.BOTTOM)

# set up matplotlib animation
      interval = 1
      BDAnim = anim.FuncAnimation(figBD, BD, yieldEvt_fromQ,
                         interval=interval, init_func=BD.init,
                         blit=True, fargs=None, repeat=True, save_count=None)
                       # save_count=None is a (temporary) work-around 
                       #     to fix memory leak in animate
      Tk.mainloop()
   
  except Exception as e:
    print('*==* mpBDisplay: terminating')
    print(e)
  sys.exit()
