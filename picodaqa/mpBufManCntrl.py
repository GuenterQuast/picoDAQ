# -*- coding: utf-8 -*-

'''Text display in TKinter window'''

from __future__ import print_function, division, unicode_literals
from __future__ import absolute_import

import sys, time, numpy as np
import threading, multiprocessing as mp

if sys.version_info[0] < 3:
  import Tkinter as Tk
  import tkMessageBox as mbox
else:
  import tkinter as Tk
  from tkinter import messagebox as mbox

import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt, matplotlib.animation as anim

# import plotBufManInfo class
from .plotBufManInfo import *

def mpBufManCntrl(Qcmd, Qlog, Qinfo, maxRate = 100. , interval = 1000.):
  '''show Buffer Manager logging messages and rate history and command buttons
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

  def cmdPause():
    Qcmd.put('P')

  def cmdResume():
    Qcmd.put('R')

  def cmdStop():
    Qcmd.put('S')

  def cmdEnd():
    Qcmd.put('E')
 
  # a simple clock
  def clkLabel(TkLabel):
     t0=time.time()
     def clkUpdate():
       dt = int(time.time() - t0)
       datetime = time.strftime('%y/%m/%d %H:%M',time.localtime(t0))
       TkLabel.config(text = 'started ' + datetime + \
                      '   T=' + str(dt) + 's  ' )
       TkLabel.after(1000, clkUpdate)
     clkUpdate()

# ------- executable part -------- 

# generate window Buttons, graphics and text display 
  Tkwin = Tk.Tk()
  Tkwin.wm_title("Buffer Manager Information")

# handle destruction of top-level window
  def _delete_window():
    if mbox.askokcancel("Quit", "Really destroy BufManCntrl window ?"):
       print("Deleting BufManCntrl window")
       Tkwin.destroy()
  
  Tkwin.protocol("WM_DELETE_WINDOW", _delete_window)

# Comand buttons
  frame = Tk.Frame(master=Tkwin)
  frame.grid(row=0, column=8)
  frame.pack(padx=5, side=Tk.BOTTOM)

  buttonE = Tk.Button(frame, text='EndRun', fg='red', command=cmdEnd)
  buttonE.grid(row=0, column=8)

  blank = Tk.Label(frame, width=7, text="")
  blank.grid(row=0, column=7)

  clock = Tk.Label(frame)
  clock.grid(row=0, column=5)

  blank2 = Tk.Label(frame, width=7, text="")
  blank2.grid(row=0, column=4)

  buttonS = Tk.Button(frame, text=' Stop ', fg='purple', command=cmdStop)
  buttonS.grid(row=0, column=3)

  buttonR = Tk.Button(frame, text='Resume', fg='blue', command=cmdResume)
  buttonR.grid(row=0, column=2)

  buttonP = Tk.Button(frame, text='Pause ', fg='blue', command=cmdPause)
  buttonP.grid(row=0, column=1)

  blank3 = Tk.Label(frame, width=7, text="")
  blank3.grid(row=0, column=0)

#
# graphics display 
  BMi = plotBufManInfo(Qinfo, maxRate, interval)
  figBMi = BMi.fig
  canvas = FigureCanvasTkAgg(figBMi, master=Tkwin)
  canvas.draw()
  canvas.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)
  canvas._tkcanvas.pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)
#
# text window
  S = Tk.Scrollbar(Tkwin)
  T = Tk.Text(Tkwin, height=10, width=100, wrap=Tk.WORD,
      bg='black', fg='aquamarine' , font='Helvetica 10')
  S.pack(side=Tk.RIGHT, fill=Tk.Y)
  T.pack(side=Tk.LEFT, fill=Tk.Y)
  S.config(command=T.yview)
  T.config(yscroll=S.set)

  try:
# start display of active time
    clkLabel(clock)

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
    Tk.mainloop()
  except:
    print('*==* mpBufManInfo: termination signal received')
  sys.exit()
