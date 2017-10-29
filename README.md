# picoDAQ

*python* Data AcQuisition and analysis with PicoScope usb-oscilloscopes

The *usb*-oscilloscope series PicoSpope by Pico Technology 
(see https://www.picotech.com)
offers universal instruments that come with great software support, not only a graphical interface offering the functionality known from oscilloscopes, 
but - most importantly for this project - also with a software development kit
(*SDK*) which makes it possible to use the devices with a wide range of
high-level languages. 

Provided here is a data acquisition system as is needed to record, 
analyse, classify and count the occurrence of wave forms such as provided 
for example by single-photon counters or typical detectors common in 
nuclear, particle physics and astro particle-physics.

This project is a first prototype towards the goal of acquiring,
analysing and counting the occurrence of typical electrical waveforms
resulting from the registered occurrence of an 'event' in a one-channel,
single particle detector such as photo tubes, Geiger counters, avalanche
photo diodes or SiPMs.

The random nature of such processes and the need to keep read-out dead 
times low requires an input buffer and a buffer manager running as a 
background process. Data are provided via the buffer manager 
interface to several consumer processes to analyse, check or visualise 
data and analysis results. Such consumers may be obligatory ones, 
i. e. data acquisition pauses if all input buffers are full and an 
obligatory consumer is still busy processing. A second type of random 
consumers receives an event copy from the buffer manager upon request, 
without pausing the data acquisition process. Typical examples of 
random consumers are displays of a subset of the wave forms or of 
intermediate analysis results. Examples for such consumers are provided
as part of this package, running either as a 'thread' within the python  
interpreter or as subprocesses using the 'multiprocessing' package.


This project originated as a demonstration to analyse pulses from a 
photomultiplier (PM) or a Silicon Photo Multiplier (SiPM) registering  
optical signals from  a detector - a coffeepot with water in the 
simplest case. 


**Requirements**:

  - *SDK* by Pico Technology, https://www.picotech.com/downloads
  - *python* bindings of the *pico-python* project by Colin O'Flynn
    and Mark Harfouche, https://github.com/colinoflynn/pico-python

  Graphical displays are implemented with *matplotlib*.

  Code was tested with PicoScope device classes PS2000a and PS4000
  under Ubuntu and openSUSE Leap.


implemented **Functions**:

   class *picoConfig*:

      - set up PicoScope channel ranges and trigger
      - set up the internal signal generator
      - PicoScope configuration read from *json* file
      - data acquisition of raw data from device

  class *BufferMan*:

      - acquire data (implemented as background thread)
      - manage event data buffer and distribute to consumers

      *obligatory* consumers: data acquisition pauses until consumer done

      *random* consumers: receive a copy of one event, data acquisition 
      continues

  module *AnimatedInstruments*

      - examples of animated graphical devices: a Buffer Manager display
        (using class *plotBufManInfo), a VoltMeter (class *VoltMeter*),
         an Oscilloscope (class *Ocscilloscope* and a Ratemeter
         (class *RMeter*). The module must run as a *python* *thread* in
         the same *python* interpreter as *BufferMan*

  module *mpOsci*

      - runs an instance of *Oscilloscpe* as a subprocess, and receives
        data from *BufferMan* via a multiprocessing Queue.

 module *mpRMeter* 

      - runs an instance of the *RMeter* class as a subprocess, receiving
        data from *BufferMan* via a multiprocessing Queue.


The example *picoDACtest.py* gives an example of how to use all of the
above. For a full demo, connect the output of a PicoScope's signal 
generator to channel B, and eventually an open cable to Channel A to 
see random noise. Use the configuration file *picoDemo.json*. 

**Installation**

This python code is compatible with *python* versions 2.7 and 3.5.
The low-level drivers and C-libraries contained in the Pico Technology
Software Development Kit are required, together with the *python* bindings
of the *pico-python* project, see the installation instructions there.
*picoDAQ* presently consists of an example *python* script (*picoDAQtest.py*),
*.json* files with configuration examples and the modules in directory *picodaqa* mentioned above. After downloading, start from the command line, e. g. *python picoDAQtest picoDemo.json*.

