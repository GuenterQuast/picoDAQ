# -*- coding: utf-8 -*-

'''Text display in TKinter window'''

from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import sys, time, numpy as np
import threading, multiprocessing as mp

if sys.version_info[0] < 3:
  import Tkinter as Tk
else:
  import tkinter as Tk

import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt, matplotlib.animation as anim

# import plotBufManInfo class
from .plotBufManInfo import *

def mpBufManInfo(Qlog, Qinfo, maxRate = 100. , interval = 1000.):
  '''show Buffer Manager logging messages and rate history
    Args:
      Qlog:     multiprocessing.Queue() for log-info  
      Qinfo:    multiprocessing.Queue() for status info
      maxrate: maximum rate for y-axis
      interval: update interval
  '''

  def wrtoLog(T):
    while True:
      T.insert(Tk.END, Qlog.get()+'\n' )
      T.see("end")
      time.sleep(0.01)

  def sequence_gen():
  # generator for sequence of integers
    i=0
    while True:
      i+=1
      yield i
    return
    
# ------- executable part -------- 

# generate window for graphics and text display 
  Tkwin = Tk.Tk()
  Tkwin.wm_title("Buffer Manager Information")

# quit button
  button = Tk.Button(master=Tkwin, text='Quit', command=sys.exit)
  button.pack(side=Tk.BOTTOM)
#
# graphics display 
  BMi = plotBufManInfo(Qinfo, maxRate, interval)
  figBMi = BMi.fig
  canvas = FigureCanvasTkAgg(figBMi, master=Tkwin)
  canvas.show()
  canvas.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)
  canvas._tkcanvas.pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)
#
# text window
  S = Tk.Scrollbar(Tkwin)
  T = Tk.Text(Tkwin, height=10, width=100, wrap=Tk.WORD,
       bg='black', fg='cyan' )
  S.pack(side=Tk.RIGHT, fill=Tk.Y)
  T.pack(side=Tk.LEFT, fill=Tk.Y)
  S.config(command=T.yview)
  T.config(yscroll=S.set)

# start an update-process for logging information as thread
#    print("starting update thread")
  wrthread = threading.Thread(target=wrtoLog,
                              args=(T, ) ) 
  wrthread.daemon = True
  wrthread.start()

# set up matplotlib animation for rate history
  BMiAnim = anim.FuncAnimation(figBMi, BMi, sequence_gen,
                     interval=interval, init_func=BMi.init,
                     blit=True, fargs=None, repeat=True, save_count=None) 
                         # save_count=None is a (temporary) work-around 
                         #     to fix memory leak in animate
  try:
    Tk.mainloop()
  except:
    print('*==* mpBufManInfo: termination signal received')
  sys.exit()
