from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import time, numpy as np
from scipy.signal import argrelmax
from multiprocessing import Queue

# open a logfile
datetime=time.strftime('%y%m%d-%H%M')
logf = open('pF'+datetime+'.dat', 'w', 1)
def printl(s, logfile=logf):
  '''print to logfile'''
  print(s, file=logfile)

def setRefPulse(dT):
  '''generate reference pulse shape for convolution filter'''
  # pulse parameters
  taur = 20E-9 # rise time in sec
  tauf = 140E-9 # fall-off time in sec
  pheight = 0.025 # pulse height in Volt

  # helper function 
  def sigshape(t):
  # compute triangular shape for negative, unipolar pulse
    if t<=taur:
      return - t/taur * pheight
    elif t >= taur + tauf:
      return 0.
    else:
      return pheight * ((t-taur)/tauf - 1.)

  l = np.int32( (taur+tauf)/dT +0.5) + 1  
  ti = np.linspace(0, taur+tauf, l)    
  rp = np.zeros(l)
  for i, t in enumerate(ti):
    rp[i] = sigshape(t)
  return l, rp


def pulseFilter(BM, filtRateQue = None, verbose=1):
  '''
    Find a pulse similar to a template pulse using cross-correlatation
    of signal and template pulse

      - implemented as an obligatory consumer, i.e.  sees all data
      - cleaning of detected pulses in second step by
        subtracting the pulse mean to increase sensitivity to the shape     
  '''

  if not BM.ACTIVE: sys.exit(1)
# register with Buffer Manager
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
  evcnt=0
  evacc=0
  Ndble=0
  T0 = time.time()
  while BM.ACTIVE:
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
            VSig[iC].append(min(evd)) # signal Voltage
            TSig[iC].append(idx*dT)   # signal Time in 
   #    -- end loop over pulse candidates
        NSig.append( len(idSig[iC]) )
   #  -- end for loop over channels

   # check for coincidence of the two channels:
      if NChan == 1 and NSig[0]:  # one valid pulse found, accept event
        tevt = TSig[0][0]
        evacc +=1
        accepted = True
      elif NChan==2 and NSig[0] and NSig[1]: 
        if abs(idSig[0][0]-idSig[1][0]) <= 2: # coincidence in time <= 2 counts
          tevt = (TSig[0][0]+TSig[1][0])/2.
          evacc +=1
          accepted = True
          if verbose > 1:
            print ('*==* pulseFilter: coincidence seen', 
                    evacc, tevt, VSig[0][0], VSig[1][0])  
     #-- end if coincidence

      if accepted:
    #  check for double pulse on either channel
        delT2=np.zeros(NChan)
        sig2=np.zeros(NChan)
        for iC in range(NChan):
          if NSig[iC]==2: 
            doublePulse = True
            delT2[iC]=(TSig[iC][1]-tevt)*1E6
            sig2[iC]=VSig[iC][1]
     #-- end if accepted
      if doublePulse:
        Ndble += 1
        s = '%i, %i, %.4g, %.4g, %.3g, %.3g'\
             %(evacc, Ndble, delT2[0], delT2[1], sig2[0], sig2[1])
        printl(s)
        if verbose: 
          print('*==* PulseFilter: evNr, evDble, dT2i, sig2i: ' + s)
     #-- end if doublePulse

      if(verbose and evcnt%1000==0):
          print("*==* pulseFilter: evNR %i, events accepted %i"%(evNr, evacc))
    # provide information mecessary for RateMeter
      if filtRateQue is not None and filtRateQue.empty(): 
        filtRateQue.put( (evacc, evTime) ) 

#   -- end if e!=None  

#    introduce random wait time to mimick processing activity
#    time.sleep(-0.25 * np.log(np.random.uniform(0.,1.)) )
 #-- end BM.ACTIVE
  logf.close()
  return
#-end def pulseFilter

