#!/usr/bin/python
# -*- coding: utf-8 -*-
# script picoDAQ.py
'''
**picoDAQ** Data Aquisition Example with Picoscpe 

Demonstrate data acquisition with PicoScope usb-oscilloscpe 

  Based on python drivers by Colin O'Flynn and Mark Harfouche,
  https://github.com/colinoflynn/pico-python

  tested with  PS2000a and PS4000

  Functions:
 
  - set up PicoScope channel ranges and trigger
  - PicoScope configuration optionally from json file
  - acquire data (implemented as thread)
  - analyse and plot data:

    - DAQtest()    test speed of data acquisitin
    - VMeter       average Voltages with bar graph display
    - Osci         simple oscilloscope
  
  graphics implemented with matplotlib

  For Demo Mode:
     Connect output of signal gnerator to channel B')
     Connect open cable to Channel A \n')
'''

from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import sys, time, json, threading
import numpy as np, matplotlib.pyplot as plt
import matplotlib.animation as anim

from collections import deque

from picoscope import ps2000a
ps = ps2000a.PS2000a()  
#from picoscope import ps4000
#ps = ps2000a.PS4000()  


# --------------------------------------------------------------
#              define scope settings here
# --------------------------------------------------------------

print('\n*==* script ' + sys.argv[0] + ' executing')

# check for / read command line arguments
if len(sys.argv)==2:
  jsonfname = sys.argv[1]
  print('     scope configurtion from file ' + jsonfname)
  try:
    with open(jsonfname) as f:
      confdict=json.load(f)
  # get mandatory parameters
      picoChannels = confdict["picoChannels"]
      ChanRanges = confdict["ChanRanges"]
      Nsamples = confdict["Nsamples"]
      sampleTime = confdict["sampleTime"]
      trgChan = confdict["trgChan"]     
      trgThr = confdict["trgThr"]
      trgTyp = confdict["trgTyp"]
      frqSG = confdict["frqSG"]
  ##    print ('   *==* all required parameters successfully read from json file')
  # get optional parameters (will be initialised below)
      if "ChanModes" in confdict: ChanModes = confdict['ChanModes']
      if "trgDelay" in confdict: trgDelay=confdict["trgDelay"]
      if "trgActive" in confdict: trgActive=confdict["trgActive"]
      if "pretrig" in confdict: pretrg=confdict["pretrg"]
      if "trgTO"  in confdict: trgTO=confdict["trgTO"] 
      if "swpSG" in confdict: swpSG=confdict["swpSG"]
      if "PkToPkSG" in confdict: PkToPkSG = confdict["PkToPkSG"]
      if "waveTypeSG" in confdict: waveTypeSG = confdict["waveTypeSG"]
      if "offsetVoltageSG" in confdict: offsetVoltageSG = confdict["offsetVoltageSG"] 
      if "dwellTimeSG" in confdict: dwellTimeSG = confdict["dwellTimeSG"]
#      if "verbose" in confict: verbose = confdict["verbose"]
      if "mode" in confdict: mode = confdict["mode"]
      if "ChanColors" in confdict: ChanColors=confdict["ChanColors"]
        
  except:
    print('     failed to read input file ' + jsonfname)
    exit(1)
else:
# use these default settings for mandatory parameters
  picoChannels = ['A', 'B'] # channels
# -- signal height:
  ChanRanges=[30E-3, 0.35]  # voltage range chan. A&B
# note: setChannel uses next largest amplitude

# -- signal timing
  Nsamples = 200  # number of samples to take 
  sampleTime = 10.E-6 # duration of sample
# note: setSamplingInterval uses next smallest sampling interval

# -- trigger configuration
  trgChan = 'A'      # trigger channel,
  trgThr = ChanRanges[0]/2.  #  threshold
  trgTyp = 'Rising'  #  type
# -- signal generator
  frqSG = 100E3
# -- end if - else config settings

# define all other parameters (if not yet done)
NChannels = len(picoChannels)
if "ChanModes" not in vars():
  ChanModes = ['AC' for i in range(NChannels)]
if "ChanOffsets" not in vars():
  ChanOffsets= [0. for i in range(NChannels)]  # voltage offsets (not yet funcional in driver)
if "trgTO" not in vars(): trgTO=1000             #  and time-out
if "trgDelay" not in vars(): trgDelay = 0        #
if "trgActive" not in vars(): trgActive = True   # no triggering if set to False
if "pretrg" not in vars(): pretrg=0.05           # fraction of samples before trigger
if "swpSG" not in vars(): swpSG = 'UpDown'

if "PkToPkSG" not in vars(): PkToPkSG = 0.4 
if "waveTypeSG" not in vars(): waveTypeSG = 'Sine'
if "stopFreqSG" not in vars(): stopFreqSG = 9 * frqSG
if "offsetVoltageSG" not in vars(): offsetVoltageSG = 0.
if "dwellTimeSG" not in vars(): 
  if frqSG > 0:
    dwellTimeSG = 10./frqSG
  else:
    dwellTimeSG = 0.
# -- printout control and colors
if "verbose" not in vars(): verbose=1            # print (detailed) info if >0 
if "ChanColors" not in vars():
  ChanColors = ['darkblue', 'darkslategrey', 'darkred', 'darkgreen']  
# 
if "mode" not in vars(): mode="notest"           # "test" "VMeter"

# --------------------------------------------------------------
# config settings are the desired inputs, actual possible settings
# (returned after setting up hardware) may be different and are stored here:
Ranges = [0., 0., 0., 0.]  # actual ranges
TSampling = 0.  # actual sampling interval
nSamples = 0    #    and number of samples to be taken

# --------------------------------------------------------------

def picoIni():
  global TSampling, nSamples, Ranges

  if verbose>1: print(__doc__)
  if verbose>0: print("Opening PicsoScope device ...")
#  ps = ps2000a.PS2000a()  
  if verbose>1:
    print("Found the following picoscope:")
    print(ps.getAllUnitInfo())

# configure oscilloscope
# 1) Time Base
  TSampling, nSamples, maxSamples = \
        ps.setSamplingInterval(sampleTime/Nsamples, sampleTime)
  if verbose>0:
    print("  Sampling interval = %.4g µs (%.g4 µs)" \
                   % (TSampling*1E6, sampleTime/Nsamples*1E6) )
    print("  Number of samples = %d (%d)" % (nSamples, Nsamples))
    #print("Maximum samples = %d" % maxSamples)
# 2) Channel Ranges
    for i, Chan in enumerate(picoChannels):
      Ranges[i] = ps.setChannel(Chan, ChanModes[i], ChanRanges[i],
                      VOffset=ChanOffsets[i], enabled=True, BWLimited=False)
      if verbose>0:
        print("  range channel %s: %.3gV (%.3gV)" % (picoChannels[i],
                                                   Ranges[i], ChanRanges[i]))
# 3) enable trigger
  ps.setSimpleTrigger(trgChan, trgThr, trgTyp,
                      trgDelay, trgTO, enabled=trgActive)    
  if verbose>0:
    print(" Trigger channel %s enabled: %.3gV %s" % (trgChan, trgThr, trgTyp))

# 4) enable Signal Generator 
  if frqSG !=0. :
    ps.setSigGenBuiltInSimple(frequency=frqSG, pkToPk=PkToPkSG,
       waveType=waveTypeSG, offsetVoltage=offsetVoltageSG,  
       sweepType=swpSG, dwellTime=dwellTimeSG, stopFreq=stopFreqSG)
    if verbose>0:
      print(" -> Signal Generator enabled: %.3gHz, +/-%.3g V %s"\
            % (frqSG, PkToPkSG, waveTypeSG) )
      print("       sweep type %s, stop %.3gHz, Tdwell %.3gs" %\
            (swpSG, stopFreqSG, dwellTimeSG) )
 
  return ps
# -- end def picoIni

def acquirePicoData(ps):
  '''
   Procucer Thread
    
     - collects data in buffers
     - provedes all acquired data to exactly one consumer 

   Communicates with consumer via collections.deque()

  '''
  global RUNNING, ibufr, Ntrig, readrate, lifefrac
#  print ('       !!! acquirePicoData starting')
  ibufw=-1     # buffer index
  Ntrig = 0    # count number of readings
  tlife = 0.   # life time
  readrate = 0.
  lifefrac = 0.

  ni = 0       # temporary variable
  T=Ns*dT # sampling period

  ts=time.time()
  
  while RUNNING:
  # sample data from Picoscope handled by instance ps
    ibufw = (ibufw + 1) % NBuffers # next write buffer
    while ibufw==ibufr:  # wait for consumer done with this buffer
      if not RUNNING: return
      time.sleep(0.001)
      
    ps.runBlock(pretrig=pretrg) #
    # wait for PicoScope to set up (~1ms)
    time.sleep(0.001) # set-up time not to be counted as "life time"
    ti=time.time()
    while not ps.isReady():
      if not RUNNING: return
      time.sleep(0.001)
    # waiting time for occurence of trigger counts as life time
    t=time.time()
    timeStamp[ibufw] = t  # store time when data became ready
    tlife += t - ti       # account life time
  # store raw data in global array 
    for i, C in enumerate(picoChannels):
      ps.getDataRaw(C, Ns, data=rawBuf[ibufw, i])
      ps.rawToV(C, rawBuf[ibufw,i], VBuf[ibufw,i], dtype=np.float32)
# alternative:
      #ps.getDataV(C, Ns, dataV=VBuf[ibufw,i], dtype=np.float32)

    Ntrig+=1
    prod_q.append( (Ntrig, ibufw) )
       
# wait for free buffer       
    while len(prod_q) == NBuffers:
      if not RUNNING: return
      time.sleep(0.001)
      
# calculate life time and read rate
    if (Ntrig - ni) == 100:
      dt=time.time()-ts
      readrate = (Ntrig-ni)/dt
      lifefrac = (readrate*T + tlife/dt)*100.      
      ts += dt
      tlife = 0.
      ni=Ntrig
  # --- end while  
  print ('          !!! acquirePicoData()  ended')
  return 0
# -- end def acquirePicoData

def getData():
  '''main Consumer Thread, request data from procuder (acquirePicoData):

       - provide all events for analysis
       - provide subset of events to "random" consumers (picoVMeter, oszi)

  '''
  global ibufr # synchronize with producer via a global variable
#              # should later be done as function call to a producer class
  t0=time.time()
  n0=0
  n=0
  while True:
    while not len(prod_q): # wait for data in producer queue
      time.sleep(0.001)
    evNr, ibufr = prod_q.popleft()

#  eventually, introduce random wait time to mimick processing time 
#    time.sleep(np.random.randint(1, 25)/1000.)

# analyze and re-distribute event data
    l_obligatory=[]
    for i, q in enumerate(request_qs):
      if len(q):
        req = q.popleft()
        if req==0:                               # return poiner to Buffer      
          consumer_qs[i].append( (evNr, ibufr) ) 
          l_obligatory.append(i)
        elif req==1:                               # return a copy of data
          evTime=timeStamp[ibufr]
          consumer_qs[i].append( (evNr, evTime, np.copy(VBuf[ibufr]) ) )
          ibufr = -1  # signal we are done wiht this event
        elif req==2:
          evTime=timeStamp[ibufr]
          consumer_qs[i].append( (evNr, evTime, np.copy(VBuf[ibufr]) ) )
          l_obligatory.append(i)
        else:
          print('!!! getData: invalid mode', req)
          exit(1)

    if ibufr != -1: # wait for new request(s) by (all) obligatory  consumer(s)
      while True:
        done = True
        for i in l_obligatory:
          if len(request_qs[i]) == 0: done = False
        if done: break
        time.sleep(0.001)        
#  now signal to producer that we are done with this event
      ibufr = -1  # signal done with data

# print event rate
    n+=1
    if n-n0 == 100:
      print('evt %i:  rate: %.3gHz   life: %.2f%%' % (n, readrate, lifefrac))
      if(evNr != n): print ("!!! ncnt != Ntrig: %i, %i"%(n,evNr) )
      n0=n

# -- end def getData


def yieldEventCopy():
# provide an event copy from getData()
   # this is useful for clients accessing only a subset of events
# 
  evCnt=0
#  evData = np.empty([NChannels, Ns], dtype=np.float32 )
  evTime = 0.
#
  rq = deque(maxlen=1)
  request_qs.append(rq )
  cq = deque(maxlen=1)
  consumer_qs.append(cq )

  evCnt=0
  evTime = 0.

  while RUNNING:
    rq.append(1)  # 1: request event data
    while not len(cq):
      time.sleep(0.01)
    evNr, evTime, evData = cq.popleft()
    #print('*==* yieldEventCopy: received event %i'%evNr)
    evCnt+=1
## client must set  ibufr = -1 if done ! 
    yield (evCnt, evTime, evData)
  
def yieldEventPtr():
# provide a pointer to event data from acquirePicoData()
   # this is useful normal clients accessing all events
  rq = deque(maxlen=1)
  request_qs.append(rq )
  cq = deque(maxlen=1)
  consumer_qs.append(cq )

  evCnt=0
  evTime = 0.

  while RUNNING:
    rq.append(0)  # 0: request an event pointer
    while not len(cq):
      time.sleep(0.01)
    evNr, ibufr = cq.popleft()
   # print('*==* yieldEventPtr: received event %i'%evNr)
    evCnt+=1
    evTime=timeStamp[ibufr]
    evData = VBuf[ibufr]
## client must set  ibufr = -1 if done ! 
    yield (evCnt, evTime, evData)
  
def obligatoryConsumer_test():
  '''
    test readout speed: do nothing, just request data from main consumer
  '''
#   set up communication queues
  rq = deque(maxlen=1)
  request_qs.append(rq )
  cq = deque(maxlen=1)
  consumer_qs.append(cq )

  while True:
    rq.append(0)  # 0: event pointer
    while not len(cq):
      time.sleep(0.01)
    evNr, ibufr = cq.popleft()
    print('*==* obligatoryConsumer_test: received event %i'%evNr)

#    introduce random wait time to mimick processing activity
    time.sleep(np.random.randint(100,2000)/1000.)
# - end def randomComsumer_test

def randomConsumer_test():
  '''
    test readout speed: do nothing, just request data from main consumer
  '''
#   set up communication queues
  rq = deque(maxlen=1)
  request_qs.append(rq )
  cq = deque(maxlen=1)
  consumer_qs.append(cq )

  while True:
    rq.append(1)  # 0: event copy
    while not len(cq):
      time.sleep(0.01)
    evNr, evTime, evData = cq.popleft()
    print('*==* randomConsumer_test: received event %i'%evNr)
#    introduce random wait time to mimick processing activity
    time.sleep(np.random.randint(100,2000)/1000.)
# - end def randomComsumer_test

def VMeter():
# Voltage measurement: average of short set of samples 
  global ibufr

  Wtime=500.    # time in ms between samplings
  Npoints = 120  # number of points for history
  ix=np.linspace(-Npoints+1, 0, Npoints) # history plot
  bwidth=0.5
  ind = bwidth + np.arange(NChannels) # bar position in bargraph for voltages
  V=np.empty(NChannels)
  stdV=np.empty(NChannels)
  Vhist=np.zeros( [NChannels, Npoints] )
  stdVhist=np.zeros( [NChannels, Npoints] )

  t0=time.time()
  print('VMeter starting')
  
  def grVMeterIni():
# set up a figure to plot actual voltage and samplings from Picoscope
    fig=plt.figure(figsize=(5., 8.) )
    fig.subplots_adjust(left=0.15, bottom=0.05, right=0.85, top=0.95,
                    wspace=None, hspace=.25)#

    axes=[]
    # history plot
    axes.append(plt.subplot2grid((7,1),(5,0), rowspan=2) )
    axes.append(axes[0].twinx())
    axes[0].set_ylim(-ChanRanges[0], ChanRanges[0])
    axes[1].set_ylim(-ChanRanges[1], ChanRanges[1])
    axes[0].set_xlabel('History')
    axes[0].set_ylabel('Chan A (V)', color=ChanColors[0])
    axes[1].set_ylabel('Chan B (V)', color=ChanColors[1])
    # barchart
    axes.append(plt.subplot2grid((7,1),(1,0), rowspan=4) )
    axbar1=axes[2]
    axbar1.set_frame_on(False)
    axbar2=axbar1.twinx()
    axbar2.set_frame_on(False)
    axbar1.get_xaxis().set_visible(False)
    axbar1.set_xlim(0., NChannels)
    axbar1.axvline(0, color=ChanColors[0])
    axbar1.axvline(NChannels, color=ChanColors[1])
    axbar1.set_ylim(-ChanRanges[0],ChanRanges[0])
    axbar1.axhline(0., color='k', linestyle='-', lw=2, alpha=0.5)
    axbar2.set_ylim(-ChanRanges[1], ChanRanges[1])
    # Voltage in Text format
    axes.append(plt.subplot2grid((7,1),(0,0)) )
    axtxt=axes[3]
    axtxt.set_frame_on(False)
    axtxt.get_xaxis().set_visible(False)
    axtxt.get_yaxis().set_visible(False)
    axtxt.set_title('Picoscope as Voltmeter', size='xx-large')

    return fig, axes, axbar1, axbar2
# -- end def grVMeterIni

  def animVMeterIni():
  # initialize objects to be animated
    global bgraph1, bgraph2, graphs, animtxt
    # a bar graph for the actual voltages
#    bgraph = axes[0].bar(ind, np.zeros(NChannels), bwidth,
#                           align='center', color='grey', alpha=0.5)
    bgraph1, = axbar1.bar(ind[0], 0. , bwidth,
                           align='center', color=ChanColors[0], alpha=0.5) 
    bgraph2, = axbar2.bar(ind[1], 0. , bwidth,
                           align='center', color=ChanColors[1], alpha=0.5) 

    # history graphs
    graphs=()
    for i, C in enumerate(picoChannels):
      g,= axes[i].plot(ix, np.zeros(Npoints), color=ChanColors[i])
      graphs += (g,)
    animtxt = axes[3].text(0.05, 0.05 , ' ',
                transform=axes[3].transAxes,
                size='x-large', color='darkblue')
#    return bgraph + graphs + (animtxt,)
    return (bgraph1,) + (bgraph2,) + graphs + (animtxt,)  

# -- end grVMeterIni()

  def animVMeter( (n, evTime, evData) ):
    global ibufr
    k=n%Npoints

    txt_t='Time  %.1fs' %(evTime-t0)            
    txt=[]
    for i, C in enumerate(picoChannels):
      V[i] = evData[i].mean()
      Vhist[i, k] = V[i]
      stdV[i] = evData[i].std()
      stdVhist[i, k] = stdV[i]
      # update history graph
      if n>1: # !!! fix to avoid permanent display of first object in blit mode
        graphs[i].set_data(ix,
          np.concatenate((Vhist[i, k+1:], Vhist[i, :k+1]), axis=0) )
      else:
        graphs[i].set_data(ix,np.zeros(Npoints))
      txt.append('Chan. %s:   %.3gV +/-%.2g' % (C, Vhist[i,k], stdVhist[i,k]) )
    # update bar chart
#    for r, v in zip(bgraph, V):
#        r.set_height(v)
    if n>1: # !!! fix to avoid permanent display of first object in blit mode
      bgraph1.set_height(V[0])
      bgraph2.set_height(V[1])
    else:  
      bgraph1.set_height(0.)
      bgraph2.set_height(0.)
    animtxt.set_text(txt_t + '\n' + txt[0] + '\n' + txt[1])

# !!! important if working with event pointer !!!
###    ibufr = -1  # signal data received, triggers next sample
#
    return (bgraph1,) + (bgraph2,) + graphs + (animtxt,)
#- -end def animVMeter
#-end def VMeter

  if verbose>0: print(' -> initializing Voltmeter graphics')
  fig, axes, axbar1, axbar2 = grVMeterIni()
  nrep=Npoints
  ani=anim.FuncAnimation(fig, animVMeter, yieldEventPtr,
                         interval=Wtime, init_func=animVMeterIni,
                         blit=True, fargs=None, repeat=True, save_count=None)
   # save_count=None is a (temporary) workaround to fix memory leak in animate
  plt.show()
                
def Oszi():
  # Oszilloscope: display channel readings in time domain

  def grOsziIni():
# set up a figure to plot samplings from Picoscope
  # needs revision if more than 2 Channels present
    fig=plt.figure(figsize=(8.0, 5.0) )
    axes=[]
# channel A
    axes.append(fig.add_subplot(1,1,1, facecolor='ivory'))
    axes[0].set_ylim(-ChanRanges[0],ChanRanges[0])
    axes[0].grid(True)
    axes[0].set_ylabel("Chan. A     Voltage (V)",
                     size='x-large',color=ChanColors[0])
    axes[0].tick_params(axis='y', colors=ChanColors[0])
# channel B
    if len(picoChannels)>1:
      axes.append(axes[0].twinx())
      axes[1].set_ylim(-ChanRanges[1],ChanRanges[1])
      axes[1].set_ylabel("Chan. B     Voltage (V)",
                     size='x-large',color=ChanColors[1])
      axes[1].tick_params(axis='y', colors=ChanColors[1])

  # time base
    axes[0].set_xlabel("Time (ms)", size='x-large') 

    trgidx=picoChannels.index(trgChan)
    trgax=axes[trgidx]
    trgcol=ChanColors[trgidx]

    axes[0].set_title("Trigger: %s, %.3gV %s" % (trgChan, trgThr, trgTyp),
                color=trgcol,
                fontstyle='italic', fontname='arial', family='monospace',
                horizontalalignment='right')
    axes[0].axhline(0., color='k', linestyle='-.', lw=2, alpha=0.5)
    trgax.axhline(trgThr, color=trgcol, linestyle='--')
    trgax.axvline(0., color=trgcol, linestyle='--')

    return fig, axes
# -- end def grOsziIni

  def animOsziIni():
  # initialize objects to be animated
    global graphs, animtxt
    graphs = ()
    for i, C in enumerate(picoChannels):
      g,= axes[i].plot(samplingTimes, np.zeros(Ns), color=ChanColors[i])
      graphs += (g,)
    animtxt = axes[0].text(0.7, 0.95, ' ', transform=axes[0].transAxes,
                   backgroundcolor='white', alpha=0.5)
    return graphs + (animtxt,)
  
  def animOszi( (n, evTime, evData) ):
    global ibufr, n0 
    if n==1: n0=0

    if n>1:    # !!! fix to avoid permanent display of first line in blit mode
      for i, C in enumerate(picoChannels):
        graphs[i].set_data(samplingTimes, evData[i])
    else:
      for i, C in enumerate(picoChannels):
        graphs[i].set_data([],[])

# !!! important if working with event pointer !!!
####    ibufr = -1  # signal data received, triggers next sample
# display rate and life time
    if n-n0 == 100:
      txt='rate: %.3gHz  life: %.0f%%' % (readrate, lifefrac)
      animtxt.set_text(txt)
      n0=n
    return graphs + (animtxt,)

  if verbose>0: print(' -> initializing graphics')
  fig, axes = grOsziIni()
  nrep=10000
  ani=anim.FuncAnimation(fig, animOszi, yieldEventCopy, interval=50,
                         init_func=animOsziIni, blit=True,
                         fargs=None, repeat=True, save_count=None)
   # save_count=None is a (temporary) workaround to fix memory leak in animate
  plt.show()
# - end def oszi     
    
if __name__ == "__main__": # - - - - - - - - - - - - - - - - - - - - - -

# initialisation
  print('-> initializing PicoScope')
  scope1 = picoIni()
  dT = TSampling  # sampling time-step
  Ns = nSamples
  # array of sampling times (in ms)
  samplingTimes =\
   1000.*np.linspace(-pretrg*Ns*dT, (1.-pretrg)*Ns*dT, Ns, endpoint=False)

  # reserve global space for data
  NBuffers= 10
  rawBuf = np.empty([NBuffers, NChannels, Ns], dtype=np.int16 )
  VBuf = np.empty([NBuffers, NChannels, Ns], dtype=np.float32 )
  timeStamp=np.empty(NBuffers)
  ibufr = -1 # index of buffer being read

  # initialize queues (collections.deque() for communication with threads
  prod_q=deque(maxlen=NBuffers) # acquireData <-> getData
  request_qs=[] # consumer request to getData
                # 0:  request event pointer, obligatory consumer
                # 1:  request event data, random consumer 
                # 2:  request event data, obligatoray consumer
  consumer_qs=[] # data from getData to consumer

  # start data acquisition thread
  if verbose>0:
    print(" -> starting data acquisition thread")   
  RUNNING = True
  thr_acquirePicoData=threading.Thread(target=acquirePicoData, args=(scope1,))
  thr_acquirePicoData.daemon=True
  thr_acquirePicoData.start()

  # start main consumer thread
  if verbose>0:
    print(" -> starting main consumer thread")   
  thr_getData=threading.Thread(target=getData)
  thr_getData.daemon=True
  thr_getData.start()

#
# --- infinite LOOP
  try:
    if mode=='test': # test readout speed
      randomConsumer_test()
    elif mode=='VMeter': # Voltmeter mode
      thr_VMeter=threading.Thread(target=VMeter)
      thr_VMeter.daemon=True
      thr_VMeter.start()
      while True:
        time.sleep(10.)
    elif mode=='osci': # Voltmeter mode
      thr_Oszi=threading.Thread(target=Oszi)
      thr_Oszi.daemon=True
      thr_Oszi.start()
      while True:
        time.sleep(10.)
    elif mode=='demo': # Voltmeter mode
      thr_Oszi=threading.Thread(target=Oszi)
      thr_Oszi.daemon=True
      thr_Oszi.start()
      while True:
        time.sleep(10.)
      else:
        print ('!!! no valid mode - exiting')
        
  except KeyboardInterrupt:
# END: code to clean up
    if verbose>0: print(' <ctrl C>  -> cleaning up ')
    RUNNING = False  # stop background data acquisition
    time.sleep(1)    #     and wait for task to finish
    scope1.stop()
    scope1.close()
    if verbose>0: print('                      -> exit ')
    exit(0)
  
