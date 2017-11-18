from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import time, numpy as np
from scipy.signal import argrelmax
from multiprocessing import Queue

def setRefPulse(dT):
  '''generate reference pulse shape for convolution filter'''
  # pulse parameters
  taur = 20E-9 # rise time in sec
  tauf = 140E-9 # fall-off time in sec
  pheight = 0.030 # pulse height in Volt

  # helper function 
  def sigshape(t):
  # compute triangular shape for negative, unipolar pulse
    if t<=taur:
      return - t/taur * pheight
    elif t >= taur + tauf:
      return 0.
    else:
      return pheight * ((t-taur)/tauf - 1.)

  l = np.int32( (taur+tauf)/dT +0.5 ) + 1  
  ti = np.linspace(0, taur+tauf, l)    
  rp = np.zeros(l)
  for i, t in enumerate(ti):
    rp[i] = sigshape(t)
  return l, rp


def pulseFilter(BM, filtRateQue = None, fileout = None, verbose=1):
  '''
    Find a pulse similar to a template pulse using cross-correlatation
    of signal and template pulse

      - implemented as an obligatory consumer, i.e.  sees all data
      - cleaning of detected pulses in second step by
        subtracting the pulse mean to increase sensitivity to the shape     
  '''

# buffermanager must be active
  if not BM.ACTIVE: 
    if verbose: print("*==* pulseFilter: Buffer Manager not active, exiting")
    sys.exit(1)

# open a logfile
  if fileout:
    datetime=time.strftime('%y%m%d-%H%M')
#    logf = open('pFilt_' + datetime+'.dat', 'w')
    logf2 = open('dpFilt_' + datetime+'.dat', 'w', 1)
    
# register this client with Buffer Manager
  myId = BM.BMregister()
  mode = 0    # obligatory consumer, request pointer to Buffer

  dT = BM.TSampling # actual sampling interval
  NChan = BM.NChannels

  lref, refp = setRefPulse(dT)
  refpm = refp - refp.mean() # mean subtracted

# calculate thresholds for correlation analysis
  pthr = np.sum(refp * refp) # norm of reference pulse
  pthrm = np.sum(refpm * refpm) # norm of mean-subtracted reference pulse
  if verbose > 1:
    print('*==* pulse Filter: reference pulse')
    print(refp)
    print('  thresholds: %.2g, %2g ' %(pthr, pthrm))

# start event loop
  evcnt=0  # events seen
  Nval=0  # events with valid pulse shape on trigger channel
  Nacc2=0  # dual coincidences
  Nacc3=0     # triple coincidences
  Ndble=0  # double pulses
  T0 = time.time()
  while BM.ACTIVE:
    validated = False
    accepted = False
    doublePulse = False
    e = BM.getEvent(myId, mode=mode)
    if e != None:
      evNr, evTime, evData = e
      evcnt+=1
      if verbose > 1:
        print('*==* pulseFilter: event Nr %i, %i events seen'%(evNr,evcnt))

# analyze signal data
  # find signal candidates by convoluting signal with reference pulse
      idSig = [] # time slice of valid pulse
      VSig = []  # signal height in Volts
      TSig = []
      NSig = []
      for iC in range(NChan):
        cor = np.correlate(evData[iC], refp, mode='valid')
        cor[cor<pthr] = pthr # set all values below threshold to threshold
        idmx, = argrelmax(cor) # find maxima 
# clean detected pulse candidates: subtract offsets
        idSig.append([])
        VSig.append([])
        TSig.append([])
        for idx in idmx:
          evd = evData[iC, idx:idx+lref]
          evdm = evd - evd.mean()  # center signal candidate around zero
          cc = np.sum(evdm *refpm) # convolution with mean-corrected reference
          if cc > pthrm:          
            idSig[iC].append(idx)
            VSig[iC].append( max(abs(evd)) ) # signal Voltage 
            TSig[iC].append(idx*dT)   # signal Time in 
   #    -- end loop over pulse candidates
        NSig.append( len(idSig[iC]) )
   #  -- end for loop over channels

      if NSig[0]:
        validated = True
        Nval +=1

# count validated and accepted events
      if NChan == 1 and validated:  # one valid pulse found, accept event
        tevt = TSig[0][0]
        accepted = True
      # coincidence of two channles if more than one counter
      elif NChan==2 and validated and NSig[1] and\
            abs(idSig[0][0]-idSig[1][0]) < 3: 
        tevt = (TSig[0][0]+TSig[1][0])/2.
        Nacc2 +=1
        accepted = True
      elif NChan==3 and validated:
        if NSig[1] and NSig[2] and\
            abs(idSig[0][0]-idSig[1][0])<3 and abs(idSig[0][0]-idSig[2][0])<3:
          accepted = True      
          tevt = (TSig[0][0]+TSig[1][0]+TSig[2][0])/3.
          Nacc3 +=1
        elif NSig[1] and abs(idSig[0][0]-idSig[1][0]) <= 2: 
          accepted = True
          tevt = (TSig[0][0]+TSig[1][0])/2.
          Nacc2 +=1
        elif NSig[2] and abs(idSig[0][0]-idSig[2][0]) <= 2: 
          accepted = True
          tevt = (TSig[0][0]+TSig[2][0])/2.
          Nacc2 +=1
     #-- end if dual coincidence
     
      if accepted:
    #  check for double pulse on either channel
        delT2=np.zeros(NChan)
        sig2=np.zeros(NChan)
        for iC in range(NChan):
          if NSig[iC] == 2 and TSig[iC][1] > tevt:
            doublePulse = True
            delT2[iC]=(TSig[iC][1]-tevt)*1E6
            sig2[iC]=VSig[iC][1]
   #-- end if accepted
        if doublePulse: Ndble += 1

# eventually store results in file(s)
# 1. all data with validated trigger signal
#      if fileout and validated:
#        print(evNr, evTime, *VSig, *TSig, sep=', ', file=logf)
# 2. double pulse 
      if fileout and doublePulse:
        print('%i, %i, %.4g, %.4g, %.3g, %.3g'\
          %(Nacc2+Nacc3, Ndble, delT2[0], delT2[1], sig2[0], sig2[1]),
                file=logf2)
# print to screen 
      if accepted and verbose > 1:
        if NChan ==1:
          print ('*==* pulseFilter  %i, %i, %.2f, %.3g, %.3g'\
                %(evcnt, Nval, tevt, VSig[0][0]) )
        elif NChan ==2:
          print ('*==* pulseFilter  %i, %i, i%, %.3g, %.3g, %.3g'\
                %(evcnt, Nval, Nacc2, tevt, VSig[0][0], VSig[1][0]) )
        elif NChan ==3:
          print ('*==* pulseFilter  %i, %i, %i, %1, %.3g'\
                %(evcnt, Nval, Nacc2, Nacc3, tevt) )

      if(verbose and evcnt%1000==0):
          print("*==* pulseFilter: evNR %i, Nval, Nacc2, Nacc3: %i, %i, %i"\
                %(evcnt, Nval, Nacc2, Nacc3))
      if verbose and doublePulse:
          s = '%i, %i, %.4g, %.4g, %.3g, %.3g'\
              %(Nacc2+Nacc3, Ndble, delT2[0], delT2[1], sig2[0],sig2[1])
          print('*==* double pulse: Nacc, Ndble, dT2i, sig2i: ' + s)

# provide information necessary for RateMeter
      if filtRateQue is not None and filtRateQue.empty(): 
        filtRateQue.put( (Nacc2+Nacc3, evTime) ) 

#   -- end if e!=None  

 #-- end BM.ACTIVE
  if fileout:
    logf.close()
    logf2.close()
  return
#-end def pulseFilter

