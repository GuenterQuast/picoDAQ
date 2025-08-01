# -*- coding: utf-8 -*-
from __future__ import print_function, division, unicode_literals
from __future__ import absolute_import

import numpy as np, time, sys, importlib

class PSconfig(object):
  '''set PicoScope configuration'''

  def __init__(self, confdict=None):
    if confdict==None: confdict={}

# set configuration parameters
# -- PicoScope model
    if "PSmodel" in confdict: 
      self.PSmodel = confdict["PSmodel"]
      if type(self.PSmodel) != type(''):
        self.PSmodel = str(self.PSmodel)
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
    if self.PSmodel == '2000':
      self.pretrig = 0.
      print('  Pretrig sampling disabled on device ', self.PSmodel)

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
# - end PSconf.__init__()

  def init(self):
# configuration parameters only known after initialisation
    # import libraries relevant to PS model
    try:
      ps_module = importlib.import_module('picoscope.ps' + self.PSmodel)
    except Exception as e:
      print('!!! PSconfig:  Error loading driver library ps'+self.PSmodel)
      print(str(e))
      print('  - exiting')
      sys.exit(1)
    try:
      ps_class = getattr(ps_module, 'PS' + self.PSmodel)
      self.picoDevice = ps_class()
    except Exception as e:
      print('!!! PSconfig:  Error initialising device')
      print(str(e))
      print('  - exiting')
      sys.exit(1)

    self.TSampling = 0.
    self.NSamples = 0.
    self.CRanges = [0., 0., 0., 0.]
   
    try: 
      self.picoIni() # run initialisation routine for device  
    except Exception as e:
      print("!!! PSconfig: Error configuring device")
      print(str(e))
      print('  - exiting')
      sys.exit(1)

   # store configuration parameters in dictionary
    self.OscConfDict = {'Channels' : self.picoChannels,
                        'NChannels' : self.NChannels,
                        'NSamples' : self.NSamples,
                        'TSampling' : self.TSampling,
                        'pretrig' : self.pretrig,
                        'CRanges' : self.CRanges,
                        'ChanOffsets': self.ChanOffsets,
                        'ChanColors': self.ChanColors,
                        'trgChan' : self.trgChan,
                        'trgActive' : self.trgActive,
                        'trgThr' : self.trgThr,
                        'trgTyp' : self.trgTyp }
# - end PSconf.init()

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
       self.sampleTime/(self.Nsamples-.1), self.sampleTime)
       ### (Nsamples-0.1) is an "empirical" fix !!!
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
         dwellTime=self.dwellTimeSG, stopFrequency=self.stopFreqSG)
      if verbose>0:
        print(prompt+"signal generator enabled: %.3gHz, +/-%.3g V %s"\
            % (self.frqSG, self.PkToPkSG, self.waveTypeSG) )
        print(prompt+"sweep type %s, stop %.3gHz, Tdwell %.3gs"\
            %(self.swpSG, self.stopFreqSG, self.dwellTimeSG) )

    self.setSamplingPars(TSampling, NSamples, CRanges) # store in config class
    # reserve static buffer for picoscope driver for storing raw data
    self.rawBuf = np.empty([self.NChannels, NSamples], dtype=np.int16 )

    # estimate set-up and transfer-overhead
    #     from maximum rate with free-running trigger
    self.toverhead = 0.00038 + self.NChannels * 0.00013

# -- end def picoIni

  def acquireDataBM(self, buffer):
    '''
    read data from device
      this part is hardware (i.e. driver) specific code for PicoScope device,
      interfaces to BufferMan.py 
      Args:
        buffer: space to store data

      Returns:
        ttrg: time when device became ready
        tlife life time of device
  '''
    if self.pretrig != 0.:
      self.picoDevice.runBlock(pretrig=self.pretrig) #
    else:
      self.picoDevice.runBlock() #
    ti=time.time()
    while not self.picoDevice.isReady():
      if not self.BM.ACTIVE.value: return None
      time.sleep(0.0001)
    # waiting time for occurence of trigger is counted as life time
    ttrg=time.time()
    # account life time, w. appr. corr. for set-up time
    tlife = ttrg - ti - self.toverhead
  # store raw data in global array 
    for i, C in enumerate(self.picoChannels):
      self.picoDevice.getDataRaw(C, self.NSamples, data=self.rawBuf[i])
      self.picoDevice.rawToV(C, self.rawBuf[i], buffer[i], dtype=np.float32)
# alternative:
     # self.picoDevice.getDataV(C, NSamples, dataV=VBuf[ibufw,i], dtype=np.float32)
    return ttrg, tlife
# - end def acquireDataBM()

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
    if self.pretrig !=0.:
      self.picoDevice.runBlock(pretrig=self.pretrig)
    else:  
     self.picoDevice.runBlock() #
    ti=time.time()
    while not self.picoDevice.isReady():
      time.sleep(0.0001)
    # waiting time for occurence of trigger is counted as life time
    ttrg=time.time()
    # account life time, w. appr. corr. for set-up time
    tlife = ttrg - ti - self.toverhead
  # store raw data in global array 
    for i, C in enumerate(self.picoChannels):
      self.picoDevice.getDataRaw(C, self.NSamples, data=self.rawBuf[i])
      self.picoDevice.rawToV(C, self.rawBuf[i], buffer[i], dtype=np.float32)
# alternative:
     # self.picoDevice.getDataV(C, NSamples, dataV=VBuf[ibufw,i], dtype=np.float32)
    return ttrg, tlife
# - end def acquirePicoData()

  def closeDevice(self):
    '''
      Close down hardwre device
    '''
    prompt = 4*' ' + 'PSconf: '
    if self.verbose: print(prompt + "closing connection to device")
    self.picoDevice.stop()
    self.picoDevice.close()
    time.sleep(0.5)


