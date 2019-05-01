# -*- coding: utf-8 -*-

'''Rate history display in TKinter window'''

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
  from tkFileDialog import asksaveasfilename
else:
  import tkinter as Tk
  from tkinter.filedialog import asksaveasfilename
    
import matplotlib.pyplot as plt, matplotlib.animation as anim

# import RMeter class
from .RMeter import *

def mpRMeter(Q, maxRate = 10. , interval = 2500., name='rate history'):
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
        e = Q.get()
        evNr = e[0]
        evTime = e[1] 
        #print('*==* yieldEvt_fromQ: received event %i' % evNr)
        cnt+=1
        evt = (cnt, evNr, evTime)
        yield evt
    except:
      print('*==* yieldEvt_fromQ: termination signal recieved')

#
# --- define button actions 
  def cmdSaveGraph(_event=None):
    try:
      filename = asksaveasfilename(initialdir='.',
                                   initialfile='Fig_Rate.png', 
                                   title='select file name')
      if filename: figRM.savefig(filename) 
    except Exception as e:
      print(str(e))
      pass
      
# ------- executable part -------- 
  print(' -> mpRMeter starting')

  RM = RMeter(maxRate, interval, name)
  figRM = RM.fig

# generate a simple window with buttons for graphics display
  root = Tk.Tk()
  root.wm_title("Rate Display")

  frame = Tk.Frame(master=root)
  frame.grid(row=0, column=5)
  frame.pack(padx=5, side=Tk.BOTTOM)
   
  button = Tk.Button(frame, text='Quit', command=sys.exit)
  button.grid(row=0, column=5)
  blank1 = Tk.Label(frame, width=5, text="")
  blank1.grid(row=0, column=3)
  buttonSvFig = Tk.Button(frame, text='saveFigure', 
                            fg='purple', command=cmdSaveGraph)
  buttonSvFig.grid(row=0, column=1)

# set up window for graphics output
  canvas = FigureCanvasTkAgg(figRM, master=root)
  canvas.draw()
  canvas.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)
  canvas._tkcanvas.pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)

# set up matplotlib animation
  try:
    RMAnim = anim.FuncAnimation(figRM, RM, yieldEvt_fromQ, 
                        init_func=RM.init, interval=interval, blit=True,
                        fargs=None, repeat=True, save_count=None)
                             # save_count=None is a (temporary) work-around 
                             #     to fix memory leak in animate
    Tk.mainloop()
   
  except:
    print('*==* mpRMeter: termination signal received')
  sys.exit()
