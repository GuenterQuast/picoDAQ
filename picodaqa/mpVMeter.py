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
  import tkMessageBox as mbox
  from tkFileDialog import asksaveasfilename
else:
  import tkinter as Tk
  from tkinter import messagebox as mbox
  from tkinter.filedialog import asksaveasfilename

import matplotlib.pyplot as plt, matplotlib.animation as anim

# import Voltmeter class
from .VoltMeter import *

def mpVMeter(Q, conf, WaitTime=500., 
                name='effective Voltage', XYmode= False, cmdQ=None):
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
    while True:
      T0 = time.time()
      if not Q.empty():
        data = Q.get()
        if type(data) != tuple:
          break # received end event
        cnt+=1
        yield (cnt,) + data
      else:
        yield None # send empty event if no new data

# guarantee correct timing 
      dtcor = interval - time.time() + T0
      if dtcor > 0. :  
        time.sleep(dtcor) 
        LblStatus.config(text=' OK ', fg = 'green')
      else:
        LblStatus.config(text='! lagging !', fg='red')

    # print('*==* yieldEvt_fromQ: received END event')          
    sys.exit()

  def cmdResume():
    cmdQ.put('R')

  def cmdPause():
    cmdQ.put('P')

  def cmdEnd():
    cmdQ.put('E')

  def cmdSave():
    try:
      filename = asksaveasfilename(initialdir='.', initialfile='VMeter.png', 
               title='select file name')
      figVM.savefig(filename) 
    except: 
      pass
 
# ------- executable part -------- 
#  print(' -> mpVMeter starting')

  VM = VoltMeter(WaitTime, conf, XYmode)
  figVM = VM.fig

# generate a simple window for graphics display as a tk.DrawingArea
  root = Tk.Tk()
  root.wm_title("Voltmeter Display")

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

  LblStatus = Tk.Label(frame, width=13, text="")
  LblStatus.grid(row=0, column=0)

  canvas = FigureCanvasTkAgg(figVM, master=root)
  canvas.draw()
  canvas.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)
  canvas._tkcanvas.pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)

# set up matplotlib animation
  tw = max(WaitTime/2., 0.5) # smaller than WaitTime to allow for processing
  VMAnim = anim.FuncAnimation(figVM, VM, yieldEvt_fromQ,
                         interval = tw, init_func = VM.init,
                         blit=True, fargs=None, repeat=True, save_count=None)
                       # save_count=None is a (temporary) work-around 
                       #     to fix memory leak in animate
  try:
    Tk.mainloop()
   
  except:
    print('*==* mpVMeter: termination signal recieved')
  sys.exit()
