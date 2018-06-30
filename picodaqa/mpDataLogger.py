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
  import tkMessageBox as mbox
  from tkFileDialog import asksaveasfilename
else:
  import tkinter as Tk
  from tkinter import messagebox as mbox
  from tkinter.filedialog import asksaveasfilename

import matplotlib.pyplot as plt, matplotlib.animation as anim

# import Voltmeter class
from .DataLogger import *


def mpDataLogger(Q, conf, WaitTime=100., name='(Veff)', cmdQ = None):
  '''effective Voltage of data passed via multiprocessing.Queue
    Args:
      Q:         multiprocessing.Queue()   
      conf:      picoConfig object
      WaitTime:  time between updates in ms
      name:      axis label
      cmdQ:      multiprocessing.Queue() for commands   
  '''

  # Generator to provide data to animation
  def yieldEvt_fromQ():
  # receives data via Queue from package mutiprocessing 
    interval = WaitTime/1000.  # in s 
    cnt = 0
    while True:
      T0 = time.time()
      if not Q.empty():
        evData = Q.get()
        # print ('Q filled ')
        if type(evData) != np.ndarray:
          break
        cnt+=1
        #print('*==* yieldEvt_fromQ: received event %i' % cnt)
        yield (cnt, evData)
      else:
        yield None # send empty event if no new data
# guarantee correct timing 
      dtcor = interval - time.time() + T0
      if dtcor > 0. :  time.sleep(dtcor) 

    print('*==* yieldEvt_fromQ: received end event')          
    sys.exit()


  def cmdResume():
    cmdQ.put('R')

  def cmdPause():
    cmdQ.put('P')

  def cmdEnd():
    cmdQ.put('E')

  def cmdSave():
    try:
      filename = asksaveasfilename(initialdir='.', 
               initialfile='DataLogger.png', 
               title='select file name')
      figDL.savefig(filename)
    except: 
      pass   

# ------- executable part -------- 
#  print(' -> mpDataLogger starting')

  DL = DataLogger(WaitTime, conf, name)
  figDL = DL.fig

# generate a simple window for graphics display as a tk.DrawingArea
  root = Tk.Tk()
  root.wm_title("Data Logger")

# handle destruction of top-level window
  def _delete_window():
    if mbox.askokcancel("Quit", "Really destroy  main window ?"):
       print("Deleting main window")
       root.destroy()
  root.protocol("WM_DELETE_WINDOW", _delete_window)

# Comand buttons
  frame = Tk.Frame(master=root)
  frame.grid(row=0, column=8)
  frame.pack(padx=5, side=Tk.BOTTOM)

  buttonE = Tk.Button(frame, text='End', fg='red', command=cmdEnd)
  buttonE.grid(row=0, column=8)

  blank = Tk.Label(frame, width=7, text="")
  blank.grid(row=0, column=7)

  clock = Tk.Label(frame)
  clock.grid(row=0, column=5)

  buttonSv = Tk.Button(frame, text=' save  ', fg='purple', command=cmdSave)
  buttonSv.grid(row=0, column=4)

  buttonS = Tk.Button(frame, text=' Pause ', fg='blue', command=cmdPause)
  buttonS.grid(row=0, column=3)

  buttonR = Tk.Button(frame, text='Resume', fg='blue', command=cmdResume)
  buttonR.grid(row=0, column=2)

  blank3 = Tk.Label(frame, width=7, text="")
  blank3.grid(row=0, column=0)

  blank4 = Tk.Label(frame, width=7, text="")
  blank4.grid(row=0, column=0)

  canvas = FigureCanvasTkAgg(figDL, master=root)
  canvas.draw()
  canvas.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)
  canvas._tkcanvas.pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)


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
