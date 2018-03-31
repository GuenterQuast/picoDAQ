#!/usr/bin/python3
# -*- coding: utf-8 -*-
# script plotDoublePulses.py


from __future__ import print_function, division, unicode_literals
from __future__ import absolute_import

import sys, time, yaml, numpy as np

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt, matplotlib.animation as anim

# animated displays running as background processes/threads
from picodaqa.Oscilloscope import *

def yieldEvt():
  cnt = 0
  for d in data:
    evt = (3, cnt, time.time(), d)
    yield evt
    cnt += 1
    print("event %i"%(cnt))
    time.sleep(twait)
  return

if __name__ == "__main__": # -----------------------------

  print('\n*==* script ' + sys.argv[0] + ' running \n')
  if len(sys.argv)==2:
    fnam = sys.argv[1]
  else: 
    fnam = 'rawDPtest.dat'
  print('    input from file ' + fnam)
  try:
    with open(fnam) as f:
      print("*= loading data")
      obj = yaml.load(f)
  except:
    print('     failed to read input file ' + fnam)
    exit(1)

  data = obj['data']
  Ndat = len(data)
  print("*= %i data sets found"%(Ndat) )
  
  plt.ion()  
  print("*= start animation")
  conf = obj['OscConf']
  Osci = Oscilloscope(conf, 'DoublePulse') 
  figOs = Osci.fig
  twait = 0.5  # time between figure updates in s

# set up matplotlib animation ...
#  osciAnim = anim.FuncAnimation(figOs, Osci, yieldEvt, 
#             init_func=Osci.init, interval=20, blit=True,
#             fargs=None, repeat=False, save_count=None)
#                 # save_count=None is a (temporary) work-around 
#                 #     to fix memory leak in animate
#  plt.show(block=True)
# ... end matplotlib animation 

# or use hand-written loop:
  Osci.init()
  cnt = 0 
  for d in data:
    cnt += 1
    evt = (3, cnt, time.time(), d)
    print("event %i"%(cnt))
    Osci(evt)
    figOs.canvas.draw()
##    figOs.savefig('DPfig%03i'%(cnt)+'.png')
    time.sleep(twait)


  print("*= end")
