# -*- coding: utf-8 -*-
# code fragment  anaDAQ.py to run inside runDAQ.py
'''
  code fragment to embed user code (in pulsfilter.py) into
   script runDAQ.py
'''

# ->>> code from here inserted as 'anaDAQ.py' in runDAQ.py

from picodaqa.mpBDisplay import mpBDisplay
from picodaqa.mpHists import mpHists

# import analysis code as library
from pulseFilter import *

# pulse shape analysis
filtRateQ = None
histQ = None
filtRateQ = mp.Queue(1) # information queue for Filter
procs.append(mp.Process(name='RMeter',
          target = mpRMeter, 
          args=(filtRateQ, 12., 2500., 'muon rate history') ) )
#               mp.Queue  rate  update interval          

histQ = mp.Queue(1) # information queue for Filter
#  book histograms and start histogrammer
Hdescriptors = []
Hdescriptors.append([0., 0.4, 50, 20., 'noise Trg. Pulse (V)', 0] )
#                   min max nbins ymax    title               lin/log
Hdescriptors.append([0., 0.8, 50, 15., 'valid Trg. Pulse (V)', 0] )
Hdescriptors.append([0., 0.8, 50, 15., 'Pulse height (V)', 0] )
Hdescriptors.append([0., 15., 45, 7.5, 'Tau (µs)', 1] )
procs.append(mp.Process(name='Hists',
          target = mpHists, 
          args=(histQ, Hdescriptors, 2000., 'Filter Histograms') ) )
#             data Queue, Hist.Desrc  interval    

VSigQ = mp.Queue(1) # information queue for Filter
mode = 2 # 0:signed, 1: abs. 2: symmetric
size = 1. # stretch factor for display
procs.append(mp.Process(name = 'ChannelSignals',
          target = mpBDisplay, 
          args=(VSigQ, PSconf, mode, size, 'Panel Signals') ) )
#               mp.Queue Chan.Conf.           name          


# run pulse analysis
cId = BM.BMregister() # get a Buffer Manager Client Id

  # pulse analysis as thread
#thrds.append(threading.Thread(target=pulseFilter,
#      args = ( BM, PSconf, cId, filtRateQ, histQ, VSigQ, True, 1) ) )
#                      BMclientId  RMeterQ  histQ  fileout verbose    

  # pulse analysis as sub-process
procs.append(mp.Process(name='pulseFilter', target=pulseFilter, 
       args = ( BM, PSconf, cId, filtRateQ, histQ, VSigQ, True, 1) ) )
#                      BMclientId  RMeterQ  histQ  fileout verbose    

#   could also run this in main thread
#pulseFilter( BM, PSconf, cId, filtRateQ, histQ, VSigQ, True, 1)  

# <<< - end of inserted code
