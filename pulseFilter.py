from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import time, numpy as np
from scipy.signal import argrelmax
from scipy.interpolate import interp1d
from multiprocessing import Queue

  # helper function to generate general unipolar or bipolar template
def trapezoidPulse(t, tr, ton, tf, toff=0., tf2=0., mode=0):
  '''
    create a single or double trapezoidal plulse, 
    normalised to pulse height one
    Args: 
     rise time, 
     on time, 
     fall time
     off-time  for bipolar pulse
     fall time for bipolar pulse
     mode: 0 single unipolar, 1: double bipolar
  '''
  ti = [0., tr, tr+ton, tr+ton+tf]
  ri = [0., 1.,     1.,     0. ]
  if mode: # for bipolar pulse
    ti = ti.append(tr+ton+tf+tf)
    ri = ri.append(-1.) 
    ti = ti.append(tr+ton+tf+tf+toff)
    ri = ri.append(-1.) 
    ti = ti.append(tr+ton+tf+tf+toff+tf2)
    ri = ri.append(0.) 

  fpulse = interp1d(ti, ri, kind='linear', copy=False, assume_sorted= True)
  return fpulse(t)

def setRefPulse(dT, taur=20E-9, tauon=12E-9, tauf=128E-9, pheight=-0.030):
  '''generate reference pulse shape for convolution filter
    Args: 
      time step
      rise time in sec
      fall-off time in sec
      pulse height in Volt
  '''

  l = np.int32( (taur+tauon+tauf)/dT +0.5 ) + 1  
  ti = np.linspace(0, taur+tauf, l)    
  rp = trapezoidPulse(ti, taur, tauon, tauf)
  rp = pheight * rp   # normalize to pulse height

  return rp


def pulseFilter(BM, filtRateQ = None, histQ = None, VSigQ = None, fileout = None, verbose=1):
  '''
    Find a pulse similar to a template pulse by cross-correlatation

      - implemented as an obligatory consumer, i.e.  sees all data
      - cleaning of detected pulses in second step by
        subtracting the pulse mean to increase sensitivity to the shape     
  '''

# buffermanager must be active
  if not BM.ACTIVE.value: 
    if verbose: print("*==* pulseFilter: Buffer Manager not active, exiting")
    sys.exit(1)

# print information to log-window via BufferManager prlog
  prlog = BM.prlog
# open a logfile
  if fileout:
    datetime=time.strftime('%y%m%d-%H%M', time.gmtime())
    logf=None
#    logf = open('pFilt_' + datetime+'.dat', 'w')
    logf2 = open('dpFilt_' + datetime+'.dat', 'w', 1)
    print("# Nacc, Ndble, Tau, delT(iChan), ... V(iChan)", 
      file=logf2)

# register this client with Buffer Manager
  myId = BM.BMregister()
  mode = 0    # obligatory consumer, request pointer to Buffer

  dT = BM.TSampling # actual sampling interval
  NChan = BM.NChannels

  refp = setRefPulse(dT)
  lref = len(refp)
  refpm = refp - refp.mean() # mean subtracted
  Fconv = refpm - 1. # function to cross-correlate with signal wave form  

# calculate thresholds for correlation analysis
  pthr = np.sum(refp * refp) # norm of reference pulse
  pthrm = np.sum(refpm * refpm) # norm of mean-subtracted reference pulse
  if verbose > 1:
    prlog('*==* pulse Filter: reference pulse')
    prlog(np.array_str(refp) )
    prlog('  thresholds: %.2g, %2g ' %(pthr, pthrm))

# initialise event loop
  evcnt=0  # events seen
  Nval=0  # events with valid pulse shape on trigger channel
  Nacc=0
  Nacc2=0  # dual coincidences
  Nacc3=0     # triple coincidences
  Ndble=0  # double pulses
  T0 = time.time()
# arrays for quantities to be histogrammed
  nTrsigs = [] #  pulse height of noise signals
  VTrsigs = [] #  pulse height of valid triggers
  VSigs = [] # pulse heights non-triggering channels
  Taus = []  # deltaT of double pulses

# event loop
  while BM.ACTIVE.value:
    validated = False
    accepted = False
    doublePulse = False
    e = BM.getEvent(myId, mode=mode)
    if e != None:
      evNr, evTime, evData = e
      evcnt+=1
      if verbose > 1:
        prlog('*==* pulseFilter: event Nr %i, %i events seen'%(evNr,evcnt))

# analyze signal data
  # find signal candidates by convoluting signal with reference pulse
      idSig = [] # time slice of valid pulse
      VSig = []  # signal height in Volts
      TSig = []
      NSig = []
      for iC in range(NChan):
        cor = np.correlate(evData[iC], refp, mode='valid')
        cor[cor<pthrm] = pthrm # set all values below threshold to threshold
        idmx, = argrelmax(cor) # find maxima 

# clean pulse candidates by requesting match with time-averaged pulse
#  to subtract constant signal parts, and collect properties of selected pulses:
        idSig.append([])
        VSig.append([])
        TSig.append([])
        for idx in idmx:
          evd = evData[iC, idx:idx+lref]
          evdm = evd - evd.mean()  # center signal candidate around zero
          cc = np.sum(evdm *refpm) # convolution with mean-corrected reference
          if cc < pthrm:
            if iC == 0: nTrsigs.append( max(abs(evd)) )
          else:   # valid pulse
            idSig[iC].append(idx)
            V = max(abs(evd)) # signal Voltage 
            VSig[iC].append(V) 
            if iC == 0: # trigger channel
              VTrsigs.append(V)
            else: 
              VSigs.append(V)
            TSig[iC].append(idx*dT)   # signal time
   #    -- end loop over pulse candidates
        NSig.append( len(idSig[iC]) )
        if NSig[iC] == 0:
          VSig[iC].append(0.) # Volts=0 if no Signal on Channel
   #  -- end for loop over channels

      if NSig[0]:   # valid signal on trigger channel
        validated = True
        Nval +=1

# count trigger validated and accepted events
      if NChan == 1 and validated:  # one valid pulse found, accept event
        tevt = TSig[0][0]
        accepted = True
        Nacc = Nval
      # require coincidence of two channles if more than one are present
      elif NChan==2 and validated and NSig[1] and\
            abs(idSig[0][0]-idSig[1][0]) < 3: 
        tevt = (TSig[0][0]+TSig[1][0])/2.
        Nacc2 +=1
        Nacc = Nacc2
        accepted = True
      elif NChan==3 and validated:
        if NSig[1] and NSig[2] and\
            abs(idSig[0][0]-idSig[1][0])<3 and abs(idSig[0][0]-idSig[2][0])<3:
          accepted = True      
          tevt = (TSig[0][0]+TSig[1][0]+TSig[2][0])/3.
          Nacc3 +=1
        elif NSig[1] and abs(idSig[0][0]-idSig[1][0]) < 3: 
          accepted = True
          tevt = (TSig[0][0]+TSig[1][0])/2.
          Nacc2 +=1
        elif NSig[2] and abs(idSig[0][0]-idSig[2][0]) < 3: 
          accepted = True
          tevt = (TSig[0][0]+TSig[2][0])/2.
          Nacc2 +=1
        Nacc = Nacc2 + Nacc3
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
        if doublePulse:
          Ndble += 1
          Taus.append(max(delT2))

# eventually store results in file(s)
# 1. all data with validated trigger signal
#      if fileout and validated:
#        print(evNr, evTime, *VSig, *TSig, sep=', ', file=logf)
# 2. double pulse 
      if fileout and doublePulse:
        if NChan==1:
          print('%i, %i, %.4g, %.4g, %.3g'\
                %(Nacc, Ndble, Taus[-1], delT2[0], sig2[0]),
                file=logf2)
        elif NChan==2:
          print('%i, %i, %.4g, %.4g, %.4g, %.3g, %.3g'\
                %(Nacc, Ndble, Taus[-1], 
                  delT2[0], delT2[1], sig2[0], sig2[1]),
                  file=logf2)
        elif NChan==3:
          print('%i, %i, %.4g, %.4g, %.4g, %.4g, %.3g, %.3g, %.3g'\
                %(Nacc, Ndble, Taus[-1], 
                  delT2[0], delT2[1], delT2[2], 
                  sig2[0], sig2[1], sig2[2]),
                  file=logf2)
# print to screen 
      if accepted and verbose > 1:
        if NChan ==1:
          prlog ('*==* pulseFilter  %i, %i, %.2f, %.3g, %.3g'\
                %(evcnt, Nacc, tevt, VSig[0][0]) )
        elif NChan ==2:
          prlog ('*==* pulseFilter  %i, %i, i%, %.3g, %.3g, %.3g'\
                %(evcnt, Nval, Nacc, tevt, VSig[0][0], VSig[1][0]) )
        elif NChan ==3:
          prlog ('*==* pulseFilter  %i, %i, %i, %i, %i, %.3g'\
                %(evcnt, Nval, Nacc, Nacc2, Nacc3, tevt) )

      if(verbose and evcnt%1000==0):
          prlog("*==* pulseFilter: evNR %i, Nval, Nacc, Nacc2, Nacc3: %i, %i, %i, %i"\
                %(evcnt, Nval, Nacc, Nacc2, Nacc3))

      if verbose and doublePulse:
          s = '%i, %i, %.4g'\
                   %(Nacc, Ndble, Taus[-1])
          prlog('*==* double pulse: Nacc, Ndble, dT ' + s)

# provide information necessary for RateMeter
      if filtRateQ is not None and filtRateQ.empty(): 
        filtRateQ.put( (Nacc, evTime) ) 
# provide information necessary for histograms
      if len(VTrsigs) and histQ is not None and histQ.empty(): 
        histQ.put( [nTrsigs, VTrsigs, VSigs, Taus] )
        nTrsigs = []
        VTrsigs = []
        VSigs = []
        Taus = []
# provide information necessary for Panel Display
      if VSigQ is not None and VSigQ.empty(): 
        peaks = [VSig[iC][0] for iC in range(NChan) ]
        VSigQ.put( peaks ) 
#   -- end if e!=None  

 #-- end BM.ACTIVE
  if fileout:
    tag = "# pulseFilter Summary: " 
    if logf: 
      print(tag+"last evNR %i, Nval, Nacc, Nacc2, Nacc3: %i, %i, %i, %i"\
        %(evcnt, Nval, Nacc, Nacc2, Nacc3),
          file=logf )
      logf.close()

    if logf2: 
      print(tag+"last evNR %i, Nval, Nacc, Nacc2, Nacc3: %i, %i, %i, %i"\
        %(evcnt, Nval, Nacc, Nacc2, Nacc3),
          file=logf2 )
      print("#                       %i double pulses"%(Ndble), 
          file=logf2 )
      logf2.close()

  return
#-end def pulseFilter

