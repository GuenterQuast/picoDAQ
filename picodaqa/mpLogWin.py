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
import matplotlib.pyplot as plt, matplotlib.animation as anim

def mpLogWin(Q, name='Buffer Manager Logging Window'):
  '''show logging information
    Args:
      Q:    multiprocessing.Queue()
      name: string, Window Title   
  '''

  def wrLog(T, Q):
    while True:
      T.insert(Tk.END, Q.get()+'\n' )
      T.see("end")
      time.sleep(0.01)

# ------- executable part -------- 
#  print(' -> mpLogWin starting')

# generate a simple window for graphics display as a tk.DrawingArea
  root = Tk.Tk()
  root.wm_title(name)
  button = Tk.Button(master=root, text='Quit', command=sys.exit)
  button.pack(side=Tk.BOTTOM)
  S = Tk.Scrollbar(root)
  T = Tk.Text(root, height=15, width=90, wrap=Tk.WORD,
       bg='black', fg='orange' )
  S.pack(side=Tk.RIGHT, fill=Tk.Y)
  T.pack(side=Tk.LEFT, fill=Tk.Y)
  S.config(command=T.yview)
  T.config(yscroll=S.set)

# start an update-process as thread
#    print("starting update thread")
  wrthread = threading.Thread(target=wrLog,
                              args=(T, Q) ) 
  wrthread.daemon = True
  wrthread.start()

  try:
    Tk.mainloop()
   
  except:
    print('*==* mpLogWindow: termination signal received')
  sys.exit()
