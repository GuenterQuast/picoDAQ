# picoDAQ

*python* Data AcQuisition and analysis with PicoScope usb-oscilloscopes

The *usb*-oscilloscope series PicoSpope by Pico Technology 
(see https://www.picotech.com)
offers universal instruments that come with great software support, not only a graphical interface offering the functionality known from oscilloscopes, 
but - most importantly for this project - also with a software development kit
(*SDK*) allowing use the devices with wide range of high-level languages. 

This makes it possible to implement a data acquisition system as
is needed to record, analyse, classify and count the occurrence of wave
forms such as provided for example by single-photon counters or typical
detectors common in nuclear physics.

This project is a first prototype towards the goal of acquiring,
analysing and counting the occurrence of typical electrical wave-forms
resulting from the registered occurrence of an 'event' in a one-channel,
single particle detector such as photo tubes, Geiger counters, avalanche
photo diodes or SiPMs.

The random nature of such processes and the need to keep dead times low
requires an input buffer and a buffer manager running in as a background
thread. Data are provided via the buffer manager's interface to several
consumer processes to analyse, check or visualise data and analysis
results. Such consumers may be obligatory ones, i. e. data acquisition
pauses if all input buffers are full and an obligatory consumer is still
busy processing. A second type of random consumers receives an event copy
from the buffer manager upon request, without pausing the data acquisition
process. Typical examples of random consumers are displays of a subset
of the wave forms or of intermediate analysis results. 

Code presently tested with PicoScope device classes PS2000a and PS4000
under Ubuntu and openSUSE Leap.


**Requirements**:

  - *SDK* by Pico Technology, https://www.picotech.com/downloads
  - *python* bindings of the *pico-python* project by Colin O'Flynn
    and Mark Harfouche, https://github.com/colinoflynn/pico-python

implemented **Functions**:

  - set up PicoScope channel ranges and trigger
  - set up the internal signal generator
  - PicoScope configuration read from *json* file
  - acquire data (implemented as background thread)
  - manage event data buffer and distribute to consumers

     - **obligatory** consumers: data acquisition pauses until consumer done
     - **random** consumers: receive a copy of one event, data acquisition continues

  - analyse and plot data:
    - consumer examples:  random and obligatory types, random waits mimic  
       processing activity
    - VMeter: a simple Voltmeter, shows average voltages as numbers,
      bar graph and history plot
    - a simple Oscilloscope:  display sampled wave forms

  Graphical displays implemented with *matplotlib*

  For Demo Mode:
     Connect the output of a PicoScopes signal generator to channel B,   
     and eventually an open cable to Channel A to see random noise.

**Installation**

This python script is compatible with *python* versions 2.7 and 3.5.
The low-level drivers and C-libraries contained in the Pico Technology
Software Development Kit are required, together with the *python* bindings
of the *pico-python* project, see the installation instructions there.
*picoDAQ* presently only consists of a single *python* script and separate file
containg the buffer manager class. A number of *.json* files contain 
configurations examples. Start from the command line, e. g. *python picoDAQ picoDemo.json*.

