"""Driver and application example for Picolog 1000 data logger

   depends on pl1000 module in the picosdk package by PicoTech

   to run the example, type 

      `python3 picolog1000Config.py`
"""
#
import sys
import time
import ctypes as ct
import numpy as np
#import matplotlib.pyplot as plt
# Pico Technology libraries
from picosdk.pl1000 import pl1000 as pl
from picosdk.functions import assert_pico_ok

## helper class for timing
class DAQwait(object):
    """ class implementing sleep corrected with system time """

    def __init__(self, dt):
        """Args:
             dt: wait time in seconds
        """
        self.dt = dt
        self.lag = False  # indicate occurrence of time lag
        self.T0 = time.time()

    def __call__(self, T0=None):
        """guarantee correct timing
           Args:
             TO:   start time of action to be timed
                     if not given, take end-time of last wait
        """
        if T0 is not None:
            self.T0 = T0
        dtcor = self.dt - time.time() + self.T0
        if dtcor > 0.:
            time.sleep(dtcor)
            self.lag = False
        else:
            self.lag = True
        self.T0 = time.time()  # end of sleep = start of next interval


class picolog1000config:
    """Configuation and data acquistion from PicoLog 1012 or 1216 data logger
    """

    def __init__(self, confdict = None, verbose = 0):
        self.verbose = verbose
        print(confdict)
        self.confdict = {} if confdict is None else confdict
        self.channels = [1] if "channels" not in self.confdict else self.confdict["channels"]
        self.NSamples = 1 if "number_of_samples" not in self.confdict else self.confdict["number_of_samples"]
        self.PLchannels = []
        for c in self.channels:
            self.PLchannels.append(f"PL1000_CHANNEL_{c}")
        self.NChannels = len(self.PLchannels)
        if self.verbose:
            print(f"{self.NChannels} active channels: {self.PLchannels}")        
        # read trigger config
        self.trgActive = 0 if "trgActive" not in confdict else confdict["trgActive"]
        self.trgAuto = 0 if "trgAuto" not in confdict else confdict["trgAuto"]
        self.trgAuto_ms = 100 if "trgAuto_ms" not in confdict else confdict["trgAuto_ms"]
        self.trgChan = 1 if "trgChan" not in confdict else confdict["trgChan"]      
        self.trgFalling = 0 if "trgFalling" not in confdict else confdict["trgFalling"]      
        self.trgThreshold = 10 if "trgThreshold" not in confdict else confdict["trgThreshold"]      
        self.trgHysteresis = 10 if "trgHysteresis" not in confdict else confdict["trgHysteresis"]      
        self.trgDelay = -0.5 if "trgPretrig" not in confdict else confdict["trgPretrig"]      


    def init(self):     
        self.c_handle = ct.c_int16()
        self.status = {}
        self.c_value = ct.c_uint16()
        # open PicoLog 1000 device
        self.status["openUnit"] = pl.pl1000OpenUnit(ct.byref(self.c_handle))
        assert_pico_ok(self.status["openUnit"])
        # get maximum ADC counts
        c_maxADC = ct.c_uint16()
        self.status["maxValue"] = pl.pl1000MaxValue(self.c_handle, ct.byref(c_maxADC))
        assert_pico_ok(self.status["maxValue"])
        print(f"device found \n    maximum ADC value of device {c_maxADC.value}")
        maxInput = 2500 # 2500 mV is max. Input for 1000 series
        self.adc2mv = maxInput/c_maxADC.value

        if self.NSamples > 1:
            # set sampling interval (use max sampling of 1/µs; number of values <= 8192)
            self.noOfValues = ct.c_uint32(self.NSamples)                    # number of samples per channel
            interval = self.NSamples * self.NChannels
            self.c_usForBlock = ct.c_uint32(interval)   # time in µs for block
            channels = (ct.c_int16 * self.NChannels)(*self.channels)
            self.c_values = (ct.c_uint16 * self.noOfValues.value * self.NChannels)() # array for data
            self.c_oveflow = ct.c_uint16()  # bit field for overflows 
            self.status["setInterval"] = pl.pl1000SetInterval(
                self.c_handle,
                ct.byref(self.c_usForBlock),
                self.noOfValues,
                ct.byref(channels),
                self.NChannels
               )
            assert_pico_ok(self.status["setInterval"])
            if interval < self.c_usForBlock.value:
                 print(f"!!! sampling interval: {self.c_usForBlock.value} µs smaller than requested")
            # set trigger
            self.status["setTrigger"] = pl.pl1000SetTrigger(
                self.c_handle,
                ct.c_uint16(self.trgActive),
                ct.c_uint16(self.trgAuto),
                ct.c_uint16(self.trgAuto_ms),
                ct.c_uint16(self.trgChan),
                ct.c_uint16(self.trgFalling),
                ct.c_uint16(self.trgThreshold),
                ct.c_uint16(self.trgHysteresis),
                ct.c_float(self.trgDelay)
                )
            assert_pico_ok(self.status["setTrigger"])
            self.pl_mode = pl.PL1000_BLOCK_METHOD["BM_SINGLE"]

        self.c_value = ct.c_uint16()
        # set up array for data        
        self.data = np.zeros(self.NChannels, dtype = np.uint16)

    def __call__(self):
        if self.NSamples > 1:
            self.read_multiple_samples()
            return self.data
            
        # simple method:
        #     get a single ADC reading for channels in list PL1000Inputs
        for i, PLchan in enumerate(self.PLchannels):            
            self.status["getSingle"] = pl.pl1000GetSingle(
                self.c_handle,
                pl.PL1000Inputs[PLchan],
                ct.byref(self.c_value)
            )
            assert_pico_ok(self.status["getSingle"])
            self.data[i] = self.c_value.value * self.adc2mv
        return self.data
    
    def read_multiple_samples(self):
        """read NSamples samples per channel and average
        """
        # start readout
        self.status["run"] = pl.pl1000Run(
            self.c_handle,
            self.noOfValues.value*self.NChannels,
            self.pl_mode
        )
        if self.verbose:
            print(f"status run: {self.status['run']}")
        assert_pico_ok(self.status["run"])
        #
        # wait for data ready
        while True:
          self.status["ready"] = pl.pl1000Ready(self.c_handle, ct.byref(self.c_value))
          time.sleep(1e-6*self.NSamples)
          if(self.c_value.value):
              break
        # retrieve values 
        self.status["getValues"] = pl.pl1000GetValues(
            self.c_handle,
            ct.byref(self.c_values),
            ct.byref(self.noOfValues),
            ct.byref(self.c_oveflow),
            None
        )
        assert_pico_ok(self.status["getValues"])
        #if self.verbose:
        #    print(f"status getValues: {self.status['getValues']}")

        # average over samples per channel and convert to mV
        values = np.ctypeslib.as_array(self.c_values).flatten()
        # order is: ch1_0, ch2_0, ..., ch1_1, ch2_1, ...
        for i in range(self.NChannels):
            self.data[i] = values[i::self.NChannels].mean() * self.adc2mv

    def close(self):
        # close PicoLog 1000 device
        self.status["closeUnit"] = pl.pl1000CloseUnit(self.c_handle)
        assert_pico_ok(self.status["closeUnit"])

    
if __name__ == "__main__": # --------------------------------------------------------
    """running application example
    """
    # set read-out interval
    interval = 0.01 #
    
    # initialize device
    confd = {"channels": [1, 2, 9], "number_of_samples": 100, "trgActive": 0 }
    # confd = {"channels": [1, 2, 9], "number_of_samples": 1}
    source = picolog1000config(confd)
    source.init()

    print(f"\n --> reading from PicoLog device @ {1/interval}Hz    ...          <cntrlC to exit>")
    print("  i   time  value(s)")
    #read data in loop
    i = 0
    wait = DAQwait(interval)
    t0 = time.time()
    try:
        while True:
            v = source()
            i += 1
            if not i%10:
               print(f"{i}, {time.time()-t0:.2f}, {v}            ", end = '\r')
            wait() 
    except KeyboardInterrupt:
        print('\n' + sys.argv[0] + ': keyboard interrupt - ending ...')
    finally:
        source.close()
