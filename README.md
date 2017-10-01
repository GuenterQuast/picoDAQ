# picoDAQ

*python* example to demonstrate data acquisition with PicoScope usb-oscilloscopes

The usb-oscilloscope series PicoSpope by Pico Technology offers quite universal measurement instruments
(see https://www.picotech.com). Most importantly for this project, they come with great software, not only a graphical
interface with the usual functionality known from oscilloscopes,
but also with a software development kit (SDK) allowing to
control the devices with a wide range of high-level languages. This makes it possible to implement a data acquisition system as
is needed to record, analyse and count the occurrence of wave forms such as provided for example by single-photon counters or typical detectors common in nuclear physics.

This project is a first prototype towards the goal of acquiring,
analysing and counting the occurrence of typical electrical wave-forms as provided by single-particle detectors, including a graphical display of a subset of raw data and of the analysis results.

Code tested with PS2000a and PS4000

**Requirements:**

  - SDK by Pico Technology, https://www.picotech.com/downloads
  - *python* bindings of the *pico-python* project by Colin O'Flynn
    and Mark Harfouche, https://github.com/colinoflynn/pico-python

implemented **Functions:**

  - set up PicoScope channel ranges and trigger
  - set up the internal signal generator
  - PicoScope configuration read from json file
  - acquire data (implemented as background thread)
  - manage event data buffer and distribute to consumers

     - **obligatory** consumers: data acquisition pauses until consumer done
     - **random** consumers: receive a copy of one event, data acquisition continues

  - analyse and plot data:
    - consumer examples:    test speed of data acquisition
    - VMeter:       a simple Voltmeter, shows average voltages as numbers,
      bar graph and history plot
    - a simple Oscilloscope:  display sampled wave forms

  Graphical displays implemented with *matplotlib*

  For Demo Mode:
     Connect the output of the signal generator to channel B, and
     eventually an open cable to Channel A.

**Installation**

This python script is compatible with *python* versions 2.7 and 3.5.
The low-level drivers and C-libraries contained in the Pico Technology
Software Development Kit are required, together with the *python* bindings
of the *pico-python* project, see the installation instructions there.
*picoDAQ* presently only consists of a single *python* script and a
number of *.json* files containing configurations. Start from the command
line, e. g. *python picoDAQ picoDemo.json*.

