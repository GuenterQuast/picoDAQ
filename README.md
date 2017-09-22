# picoDAQ

  Based on python drivers for Picotech's usb oscilloscope
  series PicoScope by Colin O'Flynn and Mark Harfouche,
  tested with  PS2000 and PS4000

  Functions:
 
  - set up picoscpe channel ranges and trigger
  - PicoScope configuration optionally from json file
  - acquire data (implemented as thread)
  - analyse and plot data:

    - DAQtest()    test speed of data acquisitin
    - VMeter       average Voltages with bar graph display
    - Oszi         simple Oszilloskope
  
  graphics implemented with matplotlib

  For Demo Mode:
     Connect output of signal gnerator to channel B')
     Connect open cable to Channel A \n')
