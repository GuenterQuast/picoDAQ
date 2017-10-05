class PSconfig(object):
  '''set PicoScope configuration'''

  def __init__(self, confdict=None):
    if confdict==None: confdict={}

# set configuration parameters
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
      self.trgThr = ChanRanges[0]/2.  #  threshold
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

# control printout, colors, ...
    if "verbose" in confdict: 
      self.verbose = confdict["verbose"]
    else:
      self.verbose=1   # print (detailed) info if >0 

    if "ChanColors" in confdict: 
      self.ChanColors=confdict["ChanColors"]
    else:
      self.ChanColors = ['darkblue', 'darkslategrey', 'darkred', 'darkgreen']   
    if "mode" in confdict: 
      self.mode = confdict["mode"]
    else:
      self.mode="osci"   # "osci" "demo" "VMeter" "test" 

# configuration parameters only known after initialisation
    self.TSampling = 0.
    self.NSamples = 0.
    self.CRanges = [0.,0.,0.,0.]

  def setSamplingPars(self, dT, NSamples, CRanges):
    self.TSampling = dT    # sampling interval
    self.NSamples = NSamples # number of samples
    self.CRanges = CRanges # channel ranges
