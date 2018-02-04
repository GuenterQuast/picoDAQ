# -*- coding: utf-8 -*-
# script runDAQ.py
'''
  code fragment to embed user code (in pulsfilter.py) into
   script runDAQ.py
'''

# ->>> code from here inserted as 'anaDAQ.py' in runDAQ.py

# import analysis code as library
from pulseFilter import *

# pulse shape analysis
filtRateQ = None
histQ = None
filtRateQ = mp.Queue(1) # information queue for Filter
procs.append(mp.Process(name='RMeter',
          target = picodaqa.mpRMeter, 
          args=(filtRateQ, 12., 2500., 'muon rate history') ) )
#               mp.Queue  rate  update interval          

histQ = mp.Queue(1) # information queue for Filter
#  book histograms and start histogrammer
Hdescriptors = []
Hdescriptors.append([0., 0.4, 50, 10., 'noise Trg. Pulse (V)', 0] )
#                   min max nbins ymax    title               lin/log
Hdescriptors.append([0., 0.8, 50, 10., 'valid Trg. Pulse (V)', 0] )
Hdescriptors.append([0., 0.8, 50, 10., 'Pulse height (V)', 0] )
Hdescriptors.append([0., 7., 35, 7.5, 'Tau (µs)', 1] )
procs.append(mp.Process(name='Hists',
          target = picodaqa.mpHists, 
          args=(histQ, Hdescriptors, 2000., 'Filter Histograms') ) )
#             data Queue, Hist.Desrc  interval    

thrds.append(threading.Thread(target=pulseFilter,
      args = ( BM, filtRateQ, histQ, True, 1) ) )
#                  RMeterQ   histQ  fileout verbose    

#   could also run this in main thread
#     pulseFilter(BM, filtRateQ, verbose=1) 

# <<< - end of inserted code
