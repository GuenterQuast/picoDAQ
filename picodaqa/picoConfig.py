# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import numpy as np, time, sys

class PSconfig(object):
  '''set PicoScope configuration'''

  def __init__(self, confdict=None):
    if confdict==None: confdict={}

# set configuration parameters
# -- PicoScope model
    if "PSmodel" in confdict: 
      self.PSmodel = confdict["PSmodel"]
    else:
      self.PSmodel = '2000a' 
# -- channels to be used
    if "picoChannels" in confdict: 
      self.picoChannels = confdict["picoChannels"]
    else:
      self.picoChannels = ['A', 'B'] # channels
    self.NChannels = len(self.picoChannels)

# -- signal height:
  # note: picoscope.setChannel uses next largest amplitude
    if "ChanRanges" in confdict:
      self.ChanRanges = confdict["ChanRanges"]
    else:
      self.ChanRanges=[30E-3, 0.35]  # voltage range chan. A&B
# -- signal timing
  # note: picoscope.setSamplingInterval uses next larger value for 
    if "Nsamples" in confdict:
      self.Nsamples = confdict["Nsamples"]
    else:
      self.Nsamples = 200  # number of samples to take 
    if "sampleTime" in confdict:
      self.sampleTime = confdict["sampleTime"]
    else:
      self.sampleTime = 10.E-6 # duration of sample

# -- trigger configuration
    if "trgChan" in confdict:
      self.trgChan = confdict["trgChan"]  
    else:
      self.trgChan = 'A'      # trigger channel,
    if "trgThr" in confdict:
      self.trgThr = confdict["trgThr"]
    else:
      self.trgThr = self.ChanRanges[0]/2.  #  threshold
    if "trgTyp" in confdict:
      self.trgTyp = confdict["trgTyp"]
    else:
      self.trgTyp = 'Rising'  #  type
# -- signal generator
    if "frqSG" in confdict:
      self.frqSG = confdict["frqSG"]
    else:
      self.frqSG = 100E3
#
# get other parameters 
    if "ChanModes" in confdict: 
      self.ChanModes = confdict['ChanModes']
    else:
      self.ChanModes = ['AC' for i in range(self.NChannels)]
    if "ChanOffsets" in confdict: 
      self.ChanOffsets = confdict['ChanOffsets']
    else:
      self.ChanOffsets= [0. for i in range(self.NChannels)]  
       # voltage offsets   !!! not yet functional in driver
    if "trgDelay" in confdict: 
      self.trgDelay=confdict["trgDelay"]
    else:
      self.trgDelay = 0        #
    if "trgActive" in confdict: 
      self.trgActive=confdict["trgActive"]
    else:
      self.trgActive = True   # no triggering if set to False
    if "pretrig" in confdict: 
      self.pretrig=confdict["pretrig"]
    else:
      self.pretrig=0.05      # fraction of samples before trigger
    if "trgTO"  in confdict: 
      self.trgTO=confdict["trgTO"] 
    else:
      self.trgTO=1000             #  and time-out
# configuration of AWG
    if "swpSG" in confdict: 
      self.swpSG=confdict["swpSG"]
    else:
      self.swpSG = 'UpDown'
    if "PkToPkSG" in confdict: 
      self.PkToPkSG = confdict["PkToPkSG"]
    else:
      self.PkToPkSG = 0.4 
    if "waveTypeSG" in confdict: 
      self.waveTypeSG = confdict["waveTypeSG"]
    else:
      self.waveTypeSG = 'Sine'
    if "stopFreqSG" in confdict: 
      self.stopFreqSG = confdict["stopFreqSG"]
    else:
      self.stopFreqSG = 9 * self.frqSG
    if "dwellTimeSG" in confdict: 
      self.dwellTimeSG = confdict["dwellTimeSG"]
    else:
      if self.frqSG != 0:     
        self.dwellTimeSG = 10./self.frqSG
      else:
        self.dwellTimeSG = 0.
    if "offsetVoltageSG" in confdict: 
      self.offsetVoltageSG = confdict["offsetVoltageSG"] 
    else:
      self.offsetVoltageSG = 0.  
    if "verbose" in confdict: 
      self.verbose = confdict["verbose"]
    else:
      self.verbose=1   # print (detailed) info if >0 

# control printout, colors, ...
    if "ChanColors" in confdict: 
      self.ChanColors=confdict["ChanColors"]
    else:
      self.ChanColors = ['darkblue', 'darkslategrey', 'darkred', 'darkgreen']   

    if "mode" in confdict: 
      self.mode = confdict["mode"] # "VMeter" "test"
# - end picoConf.__init__()

  def init(self):
# configuration parameters only known after initialisation
    # import libraries relevant to PS model
    exec('from picoscope import ps'+self.PSmodel)
    exec('self.picoDevice = ps'+self.PSmodel+'.PS'+self.PSmodel+'()')  

    self.TSampling = 0.
    self.NSamples = 0.
    self.CRanges = [0., 0., 0., 0.]
   
    try: 
      self.picoIni() # run initialisation routine for device  
    except:
      print("PSconfig: Error initialising device - exit")
      sys.exit(1)
# - end picoConf.init()

  def setSamplingPars(self, dT, NSamples, CRanges):
    self.TSampling = dT    # sampling interval
    self.NSamples = NSamples # number of samples
    self.CRanges = CRanges # channel ranges

  def setBufferManagerPointer(self, BM):
    self.BM = BM

  def picoIni(self):
    ''' initialise device controlled by class PSconf '''
    verbose = self.verbose

    if verbose>1: print(__doc__)
    if verbose>1: print("  Opening PicoScope device ...")
    if verbose>1:
      print("Found the following picoscope:")
      print(self.picoDevice.getAllUnitInfo())

    prompt = 6*' ' + 'picoIni: '
# configure oscilloscope
# 1) Time Base
    TSampling, NSamples, maxSamples = \
       self.picoDevice.setSamplingInterval(\
       self.sampleTime/self.Nsamples, self.sampleTime)
    if verbose>0:
      print(prompt+"sampling interval = %.1g µs (%.1g µs)" \
                   % (TSampling*1E6, self.sampleTime*1E6/self.Nsamples ) )
      print(prompt+"number of samples = %d (%d)" % (NSamples, self.Nsamples))
      #print("  > maximum samples = %d" % maxSamples)
# 2) Channel Ranges
      CRanges=[]
      for i, Chan in enumerate(self.picoChannels):
        CRanges.append(self.picoDevice.setChannel(Chan, self.ChanModes[i], 
                   self.ChanRanges[i], VOffset=self.ChanOffsets[i], 
                   enabled=True, BWLimited=False) )
        if verbose>0:
          print(prompt+"range channel %s: %.3gV (%.3gV)" \
          %(self.picoChannels[i], CRanges[i], self.ChanRanges[i]))
          print(prompt+"channel offset %s: %.3gV"\
          %(self.picoChannels[i], self.ChanOffsets[i]))
# 3) enable trigger
    self.picoDevice.setSimpleTrigger(self.trgChan, self.trgThr, self.trgTyp,
          self.trgDelay, self.trgTO, enabled=self.trgActive)    
    if verbose>0:
      if self.trgActive:
        print(prompt+"trigger channel %s enabled: %.3gV %s" %\
          (self.trgChan, self.trgThr, self.trgTyp))
      else:
        print(prompt+"picoIni: trigger inactive")

# 4) enable Signal Generator 
    if self.frqSG !=0. :
      self.picoDevice.setSigGenBuiltInSimple(frequency=self.frqSG, 
         pkToPk=self.PkToPkSG, waveType=self.waveTypeSG, 
         offsetVoltage=self.offsetVoltageSG, sweepType=self.swpSG, 
         dwellTime=self.dwellTimeSG, stopFreq=self.stopFreqSG)
      if verbose>0:
        print(prompt+"signal generator enabled: %.3gHz, +/-%.3g V %s"\
            % (self.frqSG, self.PkToPkSG, self.waveTypeSG) )
        print(prompt+"sweep type %s, stop %.3gHz, Tdwell %.3gs"\
            %(self.swpSG, self.stopFreqSG, self.dwellTimeSG) )

    self.setSamplingPars(TSampling, NSamples, CRanges) # store in config class
    # reserve static buffer for picoscope driver for storing raw data
    self.rawBuf = np.empty([self.NChannels, NSamples], dtype=np.int16 )

# -- end def picoIni

  def acquireData(self, buffer):
    '''
    read data from device
      this part is hardware (i.e. driver) specific code for PicoScope device

      Args:
        buffer: space to store data

      Returns:
        ttrg: time when device became ready
        tlife life time of device
  '''
    self.picoDevice.runBlock(pretrig=self.pretrig) #
    # wait for PicoScope to set up (~1ms)
 #   time.sleep(0.0005) # set-up time not to be counted as "life time"
    ti=time.time()
    while not self.picoDevice.isReady():
      if not self.BM.ACTIVE: return
      time.sleep(0.0001)
    # waiting time for occurence of trigger is counted as life time
    ttrg=time.time()
    # account life time, w. appr. corr. for set-up time
    tlife = ttrg - ti - 0.00062  
  # store raw data in global array 
    for i, C in enumerate(self.picoChannels):
      self.picoDevice.getDataRaw(C, self.NSamples, data=self.rawBuf[i])
      self.picoDevice.rawToV(C, self.rawBuf[i], buffer[i], dtype=np.float32)
# alternative:
     # self.picoDevice.getDataV(C, NSamples, dataV=VBuf[ibufw,i], dtype=np.float32)
    return ttrg, tlife
# - end def acquirePicoData()
