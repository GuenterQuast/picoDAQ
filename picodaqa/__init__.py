"""

.. moduleauthor:: Guenter Quast <guenter.quast@online.de>

.. module picodaq 
   :synopsis: data acquisition and analysis with usb-oscilloscope (PicoScope
   py Pico Technologies) 

.. moduleauthor:: Guenter Quast <g.quast@kit.edu>

**picodaqa**
    *PicoScope: data qcquisition and analysis*  

    a collction of toos to aquire data from a hardware device, buffer
    and distribute data to consumer processes 

"""

# Import version info
#import ._version_info
from ._version_info import *

# Import main components
from .picoConfig import *
from .BufferMan import *
from .AnimatedInstruments import *
from .mpOsci import *
from .mpRMeter import *
from .mpLogWin import *
from .mpBufManInfo import *

_version_suffix = 'beta'  # for suffixes such as 'rc' or 'beta' or 'alpha'
__version__ = _version_info._get_version_string()
__version__ += _version_suffix
