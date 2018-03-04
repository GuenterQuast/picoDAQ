from __future__ import print_function,division,absolute_import,unicode_literals

import time, numpy as np
from scipy.signal import argrelmax
from scipy.interpolate import interp1d
from multiprocessing import Queue

  # helper function to generate general unipolar or bipolar template
def trapezoidPulse(t, tr, ton, tf, tf2=0, toff=0., tr2=0., mode=0):
  '''
    create a single or double trapezoidal plulse, 
      normalised to pulse height one
         ______
        /      \  
     _ /_ _ _ _ \_ _ _ _ _ _ _   
                 \__________/
      r    on  f f2   off  r2 

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
  # normalize neg. pulse to same integral as positive part
    voff = -(0.5*(tr+tf)+ton) / (0.5*(tf2+tr2)+toff) 
    ti = ti.append(tr+ton+tf+tf2)
    ri = ri.append(voff) 
    ti = ti.append(tr+ton+tf+tf2+toff)
    ri = ri.append(voff) 
    ti = ti.append(tr+ton+tf+tf2+toff+tr2)
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
  tp = taur + tauon + tauf
  l = np.int32( tp/dT +0.5 ) + 1  
  ti = np.linspace(0, tp, l)    
  rp = trapezoidPulse(ti, taur, tauon, tauf)
  rp = pheight * rp   # normalize to pulse height

  return rp

def pulseFilter(BM, conf, filtRateQ = None, histQ = None, VSigQ = None, fileout = None, verbose=1):
  '''
    Find a pulse similar to a template pulse by cross-correlatation

      - implemented as an obligatory consumer, i.e.  sees all data

      - pulse detection via correlation with reference pulse;

          - detected pulses are cleaned in a second step by subtracting 
           the pulse mean (increased sensitivity to pulse shape)

      - analyis proceeds in three steps:

          1. validation of pulse on trigger channel
          2. coincidences on other channels near validated trigger pulse
          3. seach for addtional pulses on any channel
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
#    logf=None
    logf = open('pFilt_' + datetime+'.dat', 'w')
    print("# EvNr, EvT, Vs ...., Ts ...T", 
      file=logf) # header line 
    logf2 = open('dpFilt_' + datetime+'.dat', 'w', 1)
    print("# Nacc, Ndble, Tau, delT(iChan), ... V(iChan)", 
      file=logf2) # header line 

# retrieve configuration parameters
  dT = conf.TSampling # get sampling interval
  idTprec = 2 # precision on time resolution of pulse search 
  dTprec = idTprec * dT  # precision on time resolution (in units of dT)
  NChan = conf.NChannels
  NSamples = conf.NSamples
  trgChan = conf.trgChan
  iCtrg = -1   # trigger channel, initialized to -1
  for i, C in enumerate(conf.picoChannels):   
    if C == conf.trgChan: 
      iCtrg = i
      break
  idT0 = int(conf.NSamples * conf.pretrig) # sample number of trigger point

# set characteristics of reference pulse for convoultion pulse search
#     unipolar pulse:
  taur = 20E-9     # rise time in (s)
  tauon = 12E-9    # hold time in (s)
  tauf = 128E-9    # fall time in (s)
#  ph = -0.030 # pulse height (V) # for SiPM panels
  ph = -0.035 # pulse height (V) # for Kamiokanne
#
  refp = setRefPulse(dT, taur, tauon, tauf, ph)
#
  lref = len(refp)
  refpm = refp - refp.mean() # mean subtracted

# calculate thresholds for correlation analysis
  pthr = np.sum(refp * refp) # norm of reference pulse
  pthrm = np.sum(refpm * refpm) # norm of mean-subtracted reference pulse
  if verbose > 1:
    prlog('*==* pulse Filter: reference pulse')
    prlog(np.array_str(refp) )
    prlog('  thresholds: %.2g, %2g ' %(pthr, pthrm))

# register this client with Buffer Manager
  myId = BM.BMregister()
  mode = 0    # obligatory consumer, request pointer to Buffer

# --- end initialisation 

# initialise event loop
  evcnt=0  # events seen
  Nval=0  # events with valid pulse shape on trigger channel
  Nacc=0
  Nacc2=0  # dual coincidences
  Nacc3=0     # triple coincidences
  Ndble=0  # double pulses
  T0 = time.time()

# arrays for quantities to be histogrammed
  hnTrSigs = [] #  pulse height of noise signals
  hvTrSigs = [] #  pulse height of valid triggers
  hVSigs = [] # pulse heights non-triggering channels
  hTaus = []  # deltaT of double pulses
#

# event loop
  while BM.ACTIVE.value:
    validated = False
    accepted = False
    doublePulse = False
    e = BM.getEvent(myId, mode=mode)
    if e == None:
      break

    evNr, evTime, evData = e
    evcnt+=1
    if verbose > 1:
      prlog('*==* pulseFilter: event Nr %i, %i events seen'%(evNr,evcnt))

# find signal candidates by convoluting signal with reference pulse
#   data structure to collect properties of selected pulses:
    idSig = [ [0, 0] for i in range(NChan)] # time slice of valid pulse
    VSig = [ [0., 0.] for i in range(NChan)]  # signal height in Volts
    TSig = [ [0., 0.] for i in range(NChan)]  # time of valid pulse
    NSig = [0 for i in range(NChan)]

# 1. validate trigger pulse
    if iCtrg >= 0:  
      cort = np.correlate(evData[iCtrg, :idT0+idTprec+lref], 
             refp, mode='valid')
      cort[cort<pthr] = pthr # set all values below threshold to threshold
      idtr = np.argmax(cort) # find index of 1st maximum 
      if idtr > idT0 + taur + tauon + idTprec:
        hnTrSigs.append(0.)
        continue #- while # no pulse near trigger, skip rest of event analysis
    # check pulse shape by requesting match with time-averaged pulse
      evdt = evData[iCtrg, idtr:idtr+lref]
      evdtm = evdt - evdt.mean()  # center signal candidate around zero
      cc = np.sum(evdtm * refpm) # convolution with mean-corrected reference
      if cc > pthrm:
        validated = True # valid trigger pulse found, store
        Nval +=1
        V = max(abs(evdt)) # signal Voltage  
        VSig[iCtrg][0] = V 
        hvTrSigs.append(V)
        T = idtr*dT*1E6      # signal time in musec
        TSig[iCtrg][0] = T 
        tevt = T  # time of event
      else:   # no valid trigger
        hnTrSigs.append( max(abs(evdt)) )
        continue #- while # skip rest of event analysis
    NSig[iCtrg] +=1

#2. find coincidences
    Ncoinc = 1
    for iC in range(NChan):
      if iC != iCtrg:
        offset = idtr - idTprec  # search around trigger pulse
    #  analyse channel to find pulse near trigger
        cor = np.correlate(evData[iC, offset:idT0+idTprec+lref], 
              refp, mode='valid')
        cor[cor<pthr] = pthr # set all values below threshold to threshold
        id = np.argmax(cor)+offset # find index of (1st) maximum 
        if id > idT0 + taur + tauon + idTprec:
          continue #- for # no pulse near trigger, skip
        evd = evData[iC, id:id+lref]
        evdm = evd - evd.mean()  # center signal candidate around zero
        cc = np.sum(evdm * refpm) # convolution with mean-corrected reference
        if cc > pthrm:
          NSig[iC] +=1
          Ncoinc += 1 # valid, coincident pulse
          V = max(abs(evd))
          VSig[iC][0] = V         # signal voltage  
          hVSigs.append(V)         
          T = id*dT*1E6 # signal time in musec
          TSig[iC][0] = T 
          tevt += T

# check wether event should be accepted 
    if (NChan == 1 and validated) or (NChan > 1 and Ncoinc >=2):
      accepted = True
      Nacc += 1
    else:
      continue #- while 

# fix event time:
    tevt /= Ncoinc
    if Ncoinc == 2:
      Nacc2 += 1
    elif Ncoinc == 3:
      Nacc3 += 1

# 3. find subsequent pulses in accepted events
    offset = idtr + lref # search after trigger pulse
    for iC in range(NChan):
      cor = np.correlate(evData[iC, offset:], refp, mode='valid')
      cor[cor<pthr] = pthr # set all values below threshold to threshold
      idmx, = argrelmax(cor)+offset # find index of maxima in evData array
# clean-up pulse candidates by requesting match with time-averaged pulse
      iacc = 0
      for id in idmx:
        evd = evData[iC, id:id+lref]
        evdm = evd - evd.mean()  # center signal candidate around zero
        cc = np.sum(evdm * refpm) # convolution with mean-corrected reference
        if cc > pthrm: # valid pulse 
          iacc+=1
          NSig[iC] += 1
          V = max(abs(evd)) # signal Voltage 
          if iacc == 1:
            VSig[iC][1] = V 
            TSig[iC][1] = id*dT*1E6   # signal time in musec
          else: 
            VSig[iC].append(V) # extend arrays if more than 1 extra pulse
            TSig[iC].append(id*dT*1E6)   
#     -- end loop over pulse candidates
#   -- end for loop over channels
     
#  statistics on double pulses on either channel
    delT2s=np.zeros(NChan)
    sig2s=np.zeros(NChan)
    sumdT2 = 0.
    N2nd = 0.
    for iC in range(NChan):
      if VSig[iC][1] > 0.:
        doublePulse = True
        N2nd += 1
        delT2s[iC] = TSig[iC][-1] - tevt  # take last pulse found 
        sig2s[iC] = VSig[iC][-1]
        sumdT2 += delT2s[iC]
    if doublePulse:
      Ndble += 1
      hTaus.append( sumdT2 / N2nd )
    
# eventually store results in file(s)
# 1. all accepted events
    if fileout and accepted:
      print('%i, %.2f'%(evNr, evTime), end='', file=logf)
      for ic in range(NChan):
        v = VSig[ic][0]
        t = TSig[ic][0]
        if v>0: t -=tevt
        print(', %.3f, %.3f'%(v,t), end='', file=logf)
      if doublePulse:
        for ic in range(NChan):
          v = VSig[ic][1]
          t = TSig[ic][1]
          if v>0: t -=tevt
          print(', %.3f, %.3f'%(v,t), end='', file=logf)
        for ic in range(NChan):
          if len(VSig[ic]) > 2:
            print(', %i, %.3f, %.3f'%(ic, VSig[ic][2],TSig[ic][2] ),
                  end='', file=logf)
      print('', file=logf)

# 2. double pulses 
    if fileout and doublePulse:
      if NChan==1:
        print('%i, %i, %.4g,   %.4g, %.3g'\
              %(Nacc, Ndble, hTaus[-1], delT2s[0], sig2s[0]),
              file=logf2)
      elif NChan==2:
        print('%i, %i, %.4g,   %.4g, %.4g,   %.3g, %.3g'\
              %(Nacc, Ndble, hTaus[-1], 
                delT2s[0], delT2s[1], sig2s[0], sig2s[1]),
                file=logf2)
      elif NChan==3:
        print('%i, %i, %.4g,   %.4g, %.4g, %.4g,   %.3g, %.3g, %.3g'\
              %(Nacc, Ndble, hTaus[-1], 
                delT2s[0], delT2s[1], delT2s[2], 
                sig2s[0], sig2s[1], sig2s[2]),
                file=logf2)
# print to screen 
    if accepted and verbose > 1:
      if NChan ==1:
        prlog ('*==* pF: %i, %i, %.2f, %.3g, %.3g'\
              %(evcnt, Nacc, tevt, VSig[0][0]) )
      elif NChan ==2:
        prlog ('*==* pF: %i, %i, i%, %.3g, %.3g, %.3g'\
               %(evcnt, Nval, Nacc, tevt, VSig[0][0], VSig[1][0]) )
      elif NChan ==3:
        prlog ('*==* pF: %i, %i, %i, %i, %i, %.3g'\
              %(evcnt, Nval, Nacc, Nacc2, Nacc3, tevt) )

    if(verbose and evcnt%1000==0):
        prlog("*==* pF: evt %i, Nval, Nacc, Nacc2, Nacc3: %i, %i, %i, %i"\
              %(evcnt, Nval, Nacc, Nacc2, Nacc3))

    if verbose and doublePulse:
        s = '%i, %i, %.4g'\
                 %(Nacc, Ndble, hTaus[-1])
        prlog('*==* double pulse: Nacc, Ndble, dT ' + s)

# provide information necessary for RateMeter
    if filtRateQ is not None and filtRateQ.empty(): 
      filtRateQ.put( (Nacc, evTime) ) 
# provide information necessary for histograms
    if len(hvTrSigs) and histQ is not None and histQ.empty(): 
      histQ.put( [hnTrSigs, hvTrSigs, hVSigs, hTaus] )
      hnTrSigs = []
      hvTrSigs = []
      hVSigs = []
      hTaus = []
# provide information necessary for Panel Display
    if VSigQ is not None and VSigQ.empty(): 
      peaks = [VSig[iC][0] for iC in range(NChan) ]
      VSigQ.put( peaks ) 

# break e == None  

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

