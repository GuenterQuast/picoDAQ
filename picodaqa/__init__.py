"""

.. moduleauthor:: Guenter Quast <guenter.quast@online.de>

.. module picodaq 
   :synopsis: data acquisition and analysis with usb-oscilloscope (PicoScope
   py Pico Technologies) 

.. moduleauthor:: Guenter Quast <g.quast@kit.edu>

**picodaqa**
    *PicoScope: data qcquisition and analysis*  

    a collction of toos to aquire data from a hardware device, 
    buffer and distribute data to consumer processes, and analyse
    waveform data 

"""

# Import version info
from ._version_info import *
# and set version 
_version_suffix = 'rc'  # for suffixes such as 'rc' or 'beta' or 'alpha'
__version__ = _version_info._get_version_string()
__version__ += _version_suffix

# Import components to be callabel at package level
__all__ = ["BufferMan","mpBufManCntrl","mpOsci","mpRMeter","mpVMeter",
            "mpBDisplay","mpHists"]


