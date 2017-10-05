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
  - manage event data and distrobute to obligatory and random consumers
  - analyse and plot data:

    - obligatoryConsumer test speed of data acquisition
    - randomConsumer     test concurrent access
    - VMeter             average Voltages with bar graph display
    - Osci               simple oscilloscope
  
  graphics implemented with matplotlib

  For Demo Mode:
     Connect output of signal gnerator to channel B')
     Connect open cable to Channel A \n')
'''

from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import sys, time, json, numpy as np, threading

# graphical devices use matplotlib
import matplotlib
matplotlib.use('tkagg')  # set backend (qt5 not running as thread in background)
import matplotlib.pyplot as plt, matplotlib.animation as anim


from picoscope import ps2000a
picoDevObj = ps2000a.PS2000a()  
#from picoscope import ps4000
#picoDevObj = ps2000a.PS4000()  

import BufferMan

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
      if "ChanOffsets" in confdict: ChanOffsets = confdict['ChanOffsets']
      if "trgDelay" in confdict: trgDelay=confdict["trgDelay"]
      if "trgActive" in confdict: trgActive=confdict["trgActive"]
      if "pretrig" in confdict: pretrig=confdict["pretrig"]
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
  ChanOffsets= [0. for i in range(NChannels)]  # voltage offsets
  #                                      (!!! not yet functional in driver)
if "trgTO" not in vars(): trgTO=1000             #  and time-out
if "trgDelay" not in vars(): trgDelay = 0        #
if "trgActive" not in vars(): trgActive = True   # no triggering if set to False
if "pretrig" not in vars(): pretrig=0.05           # fraction of samples before trigger
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
if "mode" not in vars(): mode="osci"   # "osci" "demo" "VMeter" "test" 

# --------------------------------------------------------------
# config settings are the desired inputs, actual possible settings
# (returned after setting up hardware) may be different and are stored here:
CRanges = [0., 0., 0., 0.]  # actual ranges
TSampling = 0.  # actual sampling interval
NSamples = 0    #    and number of samples to be taken

# --------------------------------------------------------------

def picoIni():
  global TSampling, NSamples, CRanges

  if verbose>1: print(__doc__)
  if verbose>0: print("Opening PicsoScope device ...")
#  ps = ps2000a.PS2000a()  
  if verbose>1:
    print("Found the following picoscope:")
    print(picoDevObj.getAllUnitInfo())

# configure oscilloscope
# 1) Time Base
  TSampling, NSamples, maxSamples = \
        picoDevObj.setSamplingInterval(sampleTime/Nsamples, sampleTime)
  if verbose>0:
    print("  Sampling interval = %.4g µs (%.4g µs)" \
                   % (TSampling*1E6, sampleTime*1E6/Nsamples ) )
    print("  Number of samples = %d (%d)" % (NSamples, Nsamples))
    #print("Maximum samples = %d" % maxSamples)
# 2) Channel Ranges
    for i, Chan in enumerate(picoChannels):
      CRanges[i] = picoDevObj.setChannel(Chan, ChanModes[i], ChanRanges[i],
                      VOffset=ChanOffsets[i], enabled=True, BWLimited=False)
      if verbose>0:
        print("  range channel %s: %.3gV (%.3gV)" % (picoChannels[i],
                                                   CRanges[i], ChanRanges[i]))
# 3) enable trigger
  picoDevObj.setSimpleTrigger(trgChan, trgThr, trgTyp,
                      trgDelay, trgTO, enabled=trgActive)    
  if verbose>0:
    print("  Trigger channel %s enabled: %.3gV %s" % (trgChan, trgThr, trgTyp))

# 4) enable Signal Generator 
  if frqSG !=0. :
    picoDevObj.setSigGenBuiltInSimple(frequency=frqSG, pkToPk=PkToPkSG,
       waveType=waveTypeSG, offsetVoltage=offsetVoltageSG,  
       sweepType=swpSG, dwellTime=dwellTimeSG, stopFreq=stopFreqSG)
    if verbose>0:
      print(" -> Signal Generator enabled: %.3gHz, +/-%.3g V %s"\
            % (frqSG, PkToPkSG, waveTypeSG) )
      print("       sweep type %s, stop %.3gHz, Tdwell %.3gs" %\
            (swpSG, stopFreqSG, dwellTimeSG) )
 
  return
# -- end def picoIni

def acquirePicoData(buffer):
  '''
  read data from device
    this part is hardware (i.e. driver) specific code for PicoScope device

    Args:
      ps:  class handling devide
      buffer: space to store data

    Returns:
      ttrg: time when device became ready
      tlife life time of device
  '''
  picoDevObj.runBlock(pretrig=pretrig) #
    # wait for PicoScope to set up (~1ms)
  time.sleep(0.001) # set-up time not to be counted as "life time"
  ti=time.time()
  while not picoDevObj.isReady():
    if not RUNNING: return -1, -1
    time.sleep(0.001)
    # waiting time for occurence of trigger is counted as life time
  ttrg=time.time()
  tlife = ttrg - ti       # account life time
  # store raw data in global array 
  for i, C in enumerate(picoChannels):
    picoDevObj.getDataRaw(C, NSamples, data=rawBuf[i])
    picoDevObj.rawToV(C, rawBuf[i], buffer[i], dtype=np.float32)
# alternative:
      #picoDevObj.getDataV(C, NSamples, dataV=VBuf[ibufw,i], dtype=np.float32)
  return ttrg, tlife
#

# - - - - some examples of consumers connected to BufferManager- - - - 

# rely on instance BM of BufferManager class
#   and initialisation of PicoScope parameters as defined in picoDAQ.py 

def obligConsumer():
  '''
    test readout speed: do nothing, just request data from buffer manager

      - an example of an obligatory consumer, sees all data
        (i.e. data acquisition is halted when no data is requested)
    
    for reasons of speed, only a pointer to the event buffer is returned
  '''
# register with Buffer Manager
  myId = BM.BMregister()
  mode = 0    # obligatory consumer, request pointer to Buffer

  evcnt=0
  while RUNNING:
    evNr, evtile, evData = BM.BMgetEvent(myId, mode=mode)
    evcnt+=1
    print('*==* obligConsumer: event Nr %i, %i events seen'%(evNr,evcnt))

#    introduce random wait time to mimick processing activity
    time.sleep(-0.25 * np.log(np.random.uniform(0.,1.)) )
  return
#-end def obligComsumer

def randConsumer():
  '''
    test readout speed: 
      does nothing except requesting random data samples from buffer manager
  '''

  # register with Buffer Manager
  myId = BM.BMregister()
  mode = 1    # random consumer, request event copy

  evcnt=0
  while RUNNING:
    evNr, evtile, evData = BM.BMgetEvent(myId, mode=mode)
    evcnt+=1
    print('*==* randConsumer: event Nr %i, %i events seen'%(evNr,evcnt))
# introduce random wait time to mimick processing activity
    time.sleep(np.random.randint(100,1000)/1000.)
# - end def randConsumer()
  return
#

def yieldVMEvent():
# provide an event copy from Buffer Manager
   # this is useful for clients accessing only a subset of events

  myId = BM.BMregister()   # register with Buffer Manager
  mode = 1              # random consumer, request event copy

  evCnt=0
  while RUNNING:
    evNr, evTime, evData = BM.BMgetEvent(myId, mode=mode)
  #  print('*==* yieldEventCopy: received event %i' % evNr)
    evCnt+=1
    yield (evCnt, evTime, evData)
  exit(1)

def yieldOsEvent():
# provide an event copy from Buffer Manager
   # this is useful for clients accessing only a subset of events

  myId = BM.BMregister()   # register with Buffer Manager
  mode = 1              # random consumer, request event copy

  evCnt=0
  while RUNNING:
    evNr, evTime, evData = BM.BMgetEvent(myId, mode=mode)
  #  print('*==* yieldEventCopy: received event %i' % evNr)
    evCnt+=1
    yield (evCnt, evTime, evData)
  exit(1)
# 
### consumer examples with graphics -----------------------------------------
#

def Instruments(mode=0):
  '''
    graphical displays of data

    - a "Voltmeter" as an obligatory consumer
    - an Oscilloscpe display  as a random consumer

  '''

  def grVMeterIni():
# set up a figure to plot actual voltage and samplings from Picoscope
    fig = plt.figure("Voltmeter", figsize=(4., 6.) )
    fig.subplots_adjust(left=0.2, bottom=0.08, right=0.8, top=0.95,
                    wspace=None, hspace=.25)
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
    axbar1.set_ylabel('Chan A (V)', color=ChanColors[0])
    axbar2.set_ylabel('Chan B (V)', color=ChanColors[1])
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
    global bgraph1, bgraph2, graphsVM, animtxtVM
    # a bar graph for the actual voltages
#    bgraph = axes[0].bar(ind, np.zeros(NChannels), bwidth,
#                           align='center', color='grey', alpha=0.5)
    bgraph1, = axbar1.bar(ind[0], 0. , bwidth,
                           align='center', color=ChanColors[0], alpha=0.5) 
    bgraph2, = axbar2.bar(ind[1], 0. , bwidth,
                           align='center', color=ChanColors[1], alpha=0.5) 

    # history graphs
    graphsVM=()
    for i, C in enumerate(picoChannels):
      g,= axesVM[i].plot(ix, np.zeros(Npoints), color=ChanColors[i])
      graphsVM += (g,)
    animtxtVM = axesVM[3].text(0.05, 0.05 , ' ',
                transform=axesVM[3].transAxes,
                size='large', color='darkblue')
#    return bgraph + graphsVM + (animtxt,)
    return (bgraph1,) + (bgraph2,) + graphsVM + (animtxtVM,)  
# -- end grVMeterIni()

  def animVMeter( (n, evTime, evData) ):
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
        graphsVM[i].set_data(ix,
          np.concatenate((Vhist[i, k+1:], Vhist[i, :k+1]), axis=0) )
      else:
        graphsVM[i].set_data(ix,np.zeros(Npoints))
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
    animtxtVM.set_text(txt_t + '\n' + txt[0] + '\n' + txt[1])
#
    return (bgraph1,) + (bgraph2,) + graphsVM + (animtxtVM,)
#- -end def animVMeter
#-end def VMeter

                
#def Osci():
  # Oscilloscope: display channel readings in time domain

  def grOsciIni():
# set up a figure to plot samplings from Picoscope
  # needs revision if more than 2 Channels present
    fig=plt.figure("Oscilloscope", figsize=(6., 4.) )
    fig.subplots_adjust(left=0.13, bottom=0.125, right=0.87, top=0.925,
                    wspace=None, hspace=.25)
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
# -- end def grOsciIni

  def animOsciIni():
  # initialize objects to be animated
    global graphsOs, animtxtOs
    graphsOs = ()
    for i, C in enumerate(picoChannels):
      g,= axesOs[i].plot(samplingTimes, np.zeros(NSamples), color=ChanColors[i])
      graphsOs += (g,)
    animtxtOs = axesOs[0].text(0.65, 0.95, ' ', transform=axesOs[0].transAxes,
                   backgroundcolor='white', alpha=0.5)
    return graphsOs + (animtxtOs,)
  
  def animOsci( (n, evTime, evData) ):
    global n0 
    if n==1: n0=0
    if n>2:    # !!! fix to avoid permanent display of first line in blit mode
      for i, C in enumerate(picoChannels):
        graphsOs[i].set_data(samplingTimes, evData[i])
    else:
      for i, C in enumerate(picoChannels):
        graphsOs[i].set_data([],[])

# display rate and life time
    if n-n0 == 50:
      txt='rate: %.3gHz  life: %.0f%%' % (BM.readrate, BM.lifefrac)
      animtxtOs.set_text(txt)
      n0=n
    return graphsOs + (animtxtOs,)
# -end animOsci
  
# - control part for graphical Instruments()
  anims=[]
  if mode==0 or mode==2:
# Voltmeter
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
    if verbose>0: print(' -> Voltmeter starting')
    figVM, axesVM, axbar1, axbar2 = grVMeterIni()

    anims.append(anim.FuncAnimation(figVM, animVMeter, yieldVMEvent,
                         interval=Wtime, init_func=animVMeterIni,
                         blit=True, fargs=None, repeat=True, save_count=None) )
   # save_count=None is a (temporary) workaround to fix memory leak in animate

  if mode==1 or mode==2:  
    if verbose>0: print(' -> Oscilloscope starting')
    figOs, axesOs = grOsciIni()

    anims.append(anim.FuncAnimation(figOs, animOsci, yieldOsEvent, interval=50,
                         init_func=animOsciIni, blit=True,
                         fargs=None, repeat=True, save_count=None))
   # save_count=None is a (temporary) workaround to fix memory leak in animate

  try:
    plt.show()
  except: 
    print ('matplotlib animate exiting ...')


if __name__ == "__main__": # - - - - - - - - - - - - - - - - - - - - - -

# initialisation
  print('-> initializing PicoScope')

  picoIni() 
  SamplingPeriod = TSampling * NSamples  
  # array of sampling times (in ms)
  samplingTimes =\
   1000.*np.linspace(-pretrig*SamplingPeriod, (1.-pretrig)*SamplingPeriod, NSamples)

# reserve global space for data
  # static buffer for picoscope driver for storing raw data
  rawBuf = np.empty([NChannels, NSamples], dtype=np.int16 )

  NBuffers= 16
  BM = BufferMan.BufferMan(NBuffers, NChannels, NSamples, acquirePicoData)

  # start data acquisition thread
  if verbose>0:
    print(" -> starting Buffer Manager Threads")   
  RUNNING = True
  BM.run()  

#
# --- infinite LOOP
  try:
    if mode=='VMeter': # Voltmeter mode
      m=0
    elif mode=='osci': # Oscilloscpe mode
      m=1
    elif mode=='demo': #  both VMeter and Oscilloscpe
      m=2
    elif mode=='test': # test consumers
      thr_randConsumer=threading.Thread(target=randConsumer )
      thr_randConsumer.daemon=True
      thr_randConsumer.start()
      thr_obligConsumer=threading.Thread(target=obligConsumer )
      thr_obligConsumer.daemon=True
      thr_obligConsumer.start()
      m=2
    else:
      print ('!!! no valid mode - exiting')
      exit(1)
    
    thr_Instruments=threading.Thread(target=Instruments, args=(m,) )
    thr_Instruments.daemon=True
    thr_Instruments.start()

# run until key pressed
    raw_input('\n                                             Press <ret> to end -> \n\n')
    if verbose: print(' ending  -> cleaning up ')
    RUNNING = False  # stop background processes
    BM.end()         # tell buffer manager that we're done
    time.sleep(2)    #     and wait for tasks to finish
    picoDevObj.stop()
    picoDevObj.close()
    if verbose>0: print('                      -> exit')
    exit(0)

#
#    while True:
#      time.sleep(10.)

  except KeyboardInterrupt:
# END: code to clean up
    if verbose>0: print(' <ctrl C>  -> cleaning up ')
    RUNNING = False  # stop background data acquisition
    BM.end()
    time.sleep(2)    #     and wait for tasks to finish
    picoDevObj.stop()
    picoDevObj.close()
    if verbose>0: print('                      -> exit')
    exit(0)
  
