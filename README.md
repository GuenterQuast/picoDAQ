# picoDAQ

*python* Data AcQuisition and analysis with PicoScope usb-oscilloscopes

The *usb*-oscilloscope series PicoSpope by Pico Technology 
(see https://www.picotech.com)
offers universal instruments that come with great software support, not only a graphical interface offering the functionality known from oscilloscopes, 
but - most importantly for this project - also with a software development kit
(*SDK*) which makes it possible to use the devices with wide range of 
high-level languages. 

Provided here is a data acquisition system as is needed to record, 
analyse, classify and count the occurrence of wave forms such as provided 
for example by single-photon counters or typical detectors common in 
nuclear, particle and astroparticle physics.

This project is a first prototype towards the goal of acquiring,
analysing and counting the occurrence of typical electrical waveforms
resulting from the registered occurrence of an 'event' in a one-channel,
single particle detector such as photo tubes, Geiger counters, avalanche
photo diodes or SiPMs.

The random nature of such processes and the need to keep dead times low
requires an input buffer and a buffer manager running as a background
process. Data are provided via the buffer manager's interface to several
consumer processes to analyse, check or visualise data and analysis
results. Such consumers may be obligatory ones, i. e. data acquisition
pauses if all input buffers are full and an obligatory consumer is still
busy processing. A second type of random consumers receives an event copy
from the buffer manager upon request, without pausing the data acquisition
process. Typical examples of random consumers are displays of a subset
of the wave forms or of intermediate analysis results. Examples are
provided for such conusmers running as a 'thread' within the python 
interpreter or as subprocesses using the 'multiprocessing' package.

Code tested with PicoScope device classes PS2000a and PS4000
under Ubuntu and openSUSE Leap.


This project originated as a demonstration to analyse pulses from a 
Photomultiplier (PM) or a Silicon Photo Multiplier (SiPM) registering  
optical signals from  a detector - a coffeepot with water in the 
simplest case. 


**Requirements**:

  - *SDK* by Pico Technology, https://www.picotech.com/downloads
  - *python* bindings of the *pico-python* project by Colin O'Flynn
    and Mark Harfouche, https://github.com/colinoflynn/pico-python

implemented **Functions**:

   class *picoConfig*:

      - set up PicoScope channel ranges and trigger
      - set up the internal signal generator
      - PicoScope configuration read from *json* file
      - data aquition of raw data from device

  class *BufferMan*:

      - acquire data (implemented as background thread)
      - manage event data buffer and distribute to consumers

      *obligatory* consumers: data acquisition pauses until consumer done

      *random* consumers: receive a copy of one event, data acquisition 
      continues

  module *AnimatedInstruments*

      - examples of animated graphical devides - a VoltMeter,   
        an Oscilloscope and a Ratemeter
  
      uses classes VoltMeter, Oscilloscope and plotBufManInfo.
  
  module *mpOsci* 

      - runs an instance of the Oscilloscpe class as a subprocess 

The examples show applications of the graphical devices and 
an implementations of obligatory and random consumers.


  Graphical displays implemented with *matplotlib*

  For Demo Mode:
     Connect the output of a PicoScopes signal generator to channel B,   
     and eventually an open cable to Channel A to see random noise.

**Installation**

This python script is compatible with *python* versions 2.7 and 3.5.
The low-level drivers and C-libraries contained in the Pico Technology
Software Development Kit are required, together with the *python* bindings
of the *pico-python* project, see the installation instructions there.
*picoDAQ* presently only consists of an example *python* script (*picoDAQtest.py*) and modules in directory *picodaqa*,
containing the configuration and buffer manager classes and a module
with the examples of animated graphical instruments implemented . 
A number of *.json* files contain configurations examples. Start from the command line, e. g. *python picoDAQtest picoDemo.json*.

