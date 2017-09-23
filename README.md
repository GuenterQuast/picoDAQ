# picoDAQ

Demonstrate data acquisition with PicoScope usb-oscilloscpe.

The usb-oscilloscopes PicoSpope by Pico Technology are quite universal
measurement instruments (see https://www.picotech.com). Most importantly
for this project, they come with great software, not only a graphical
interface with the usual functionality known from oscilloscopes, but
also with a software development kit (SDK) allowing to control the devices
with a wide range of high-level languages. This makes it possible to
implement a data acquistion system as is for example needed to record and ananlyse wave forms from randomly occuring signals, as are provided for
example by single-photon counters or detectors in nuclear physics.

This project is a first proto-type towards the goal of displaying,
analysing and counting the occurance of typical wave forms provided
by single-particle detectors.

Code tested with PS2000a and PS4000

**Requirements:**  

  - SDK by Pico Technology, https://www.picotech.com/downloads
  - *python* bindings of the *pico-pyhton* project by Colin O'Flynn
    and Mark Harfouche, https://github.com/colinoflynn/pico-python

implemented **Functions:**

  - set up PicoScope channel ranges and trigger
  - set up the internal signal generator
  - PicoScope configuration optionally from json file
  - acquire data (implemented as background thread)
  - analyse and plot data:
    - DAQtest()    test speed of data acquisition
    - VMeter       as simple Voltmeter, shows average voltages
       as numbers, bar graph and history plot
    - a simple Oscilloscope to display sampled wave forms

  Graphical displaysimplemented with matplotlib

  For Demo Mode:  
     Connect the output of the signal gnerator to channel B, and
     eventually an open cable to Channel A.

**Installation**

This python script is compatible with *python* versions 2.7 and 3.5.
The low-level drivers and C-libraries contained in the Pico Technology
Software Development Kit are required, togther with the *python* bindings
of the *pico-python* projcect, see the installation instructions there.
*picoDAQ* presently only consists of a single *pyhton* script and a
number of *.json* files containing configurations. Start from the command
line, e. g. *python picoDAQ picoDemo.json*.

