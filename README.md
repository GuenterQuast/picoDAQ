# picoDAQ
Demonstrate data acquisition with PicoScope usb-oscilloscpe 

  Based on python drivers by Colin O'Flynn and Mark Harfouche,
  https://github.com/colinoflynn/pico-python

  tested with  PS2000a and PS4000

  Functions:
 
  - set up PicoScope channel ranges and trigger
  - PicoScope configuration optionally from json file
  - acquire data (implemented as thread)
  - analyse and plot data:

    - DAQtest()    test speed of data acquisitin
    - VMeter       average Voltages with bar graph display
    - Osci         simple oscilloscope
  
  graphics implemented with matplotlib

  For Demo Mode:

     Connect output of signal gnerator to channel B, and 
     eventually an open cable to Channel A 
