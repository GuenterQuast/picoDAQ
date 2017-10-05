# - - - - some examples of consumers connected to BufferManager- - - - 

# relys on instance BM of BufferManager class
#   and initialisation of PicoScope parameters as defined in picoDAQ.py 


def obligConsumer():
  '''
    test readout speed: do nothing, just request data from buffer manager

      - an example of an obligatory consumer, sees all data
        (i.e. data acquisition is halted when no data is requested)
    
    for reasons of speed, only a pointer to the event buffer is returned
  '''
# register with Buffer Manager
  myId = BM.BMregister()
  mode = 0    # obligatory consumer, request pointer to Buffer

  evcnt=0
  while RUNNING:
    evNr, evtile, evData = BM.BMgetEvent(myId, mode=mode)
    evcnt+=1
    print('*==* obligConsumer: event Nr %i, %i events seen'%(evNr,evcnt))

#    introduce random wait time to mimick processing activity
    time.sleep(-0.25 * np.log(np.random.uniform(0.,1.)) )
  return
#-end def obligComsumer

def randConsumer():
  '''
    test readout speed: 
      does nothing except requesting random data samples from buffer manager
  '''

  # register with Buffer Manager
  myId = BM.BMregister()
  mode = 1    # random consumer, request event copy

  evcnt=0
  while RUNNING:
    evNr, evtile, evData = BM.BMgetEvent(myId, mode=mode)
    evcnt+=1
    print('*==* randConsumer: event Nr %i, %i events seen'%(evNr,evcnt))
# introduce random wait time to mimick processing activity
    time.sleep(np.random.randint(100,1000)/1000.)
# - end def randConsumer()
  return
#

def yieldVMEvent():
# provide an event copy from Buffer Manager
   # this is useful for clients accessing only a subset of events

  myId = BM.BMregister()   # register with Buffer Manager
  mode = 1              # random consumer, request event copy

  evCnt=0
  while RUNNING:
    evNr, evTime, evData = BM.BMgetEvent(myId, mode=mode)
  #  print('*==* yieldEventCopy: received event %i' % evNr)
    evCnt+=1
    yield (evCnt, evTime, evData)
  exit(1)

def yieldOsEvent():
# provide an event copy from Buffer Manager
   # this is useful for clients accessing only a subset of events

  myId = BM.BMregister()   # register with Buffer Manager
  mode = 1              # random consumer, request event copy

  evCnt=0
  while RUNNING:
    evNr, evTime, evData = BM.BMgetEvent(myId, mode=mode)
  #  print('*==* yieldEventCopy: received event %i' % evNr)
    evCnt+=1
    yield (evCnt, evTime, evData)
  exit(1)
# 
### consumer examples with graphics -----------------------------------------
#

def Instruments(mode=0):
  '''
    graphical displays of data

    - a "Voltmeter" as an obligatory consumer
    - an Oscilloscpe display  as a random consumer

  '''

  def grVMeterIni():
# set up a figure to plot actual voltage and samplings from Picoscope
    fig = plt.figure("Voltmeter", figsize=(4., 6.) )
    fig.subplots_adjust(left=0.2, bottom=0.08, right=0.8, top=0.95,
                    wspace=None, hspace=.25)
    axes=[]
    # history plot
    axes.append(plt.subplot2grid((7,1),(5,0), rowspan=2) )
    axes.append(axes[0].twinx())
    axes[0].set_ylim(-ChanRanges[0], ChanRanges[0])
    axes[1].set_ylim(-ChanRanges[1], ChanRanges[1])
    axes[0].set_xlabel('History')
    axes[0].set_ylabel('Chan A (V)', color=ChanColors[0])
    axes[1].set_ylabel('Chan B (V)', color=ChanColors[1])
    # barchart
    axes.append(plt.subplot2grid((7,1),(1,0), rowspan=4) )
    axbar1=axes[2]
    axbar1.set_frame_on(False)
    axbar2=axbar1.twinx()
    axbar2.set_frame_on(False)
    axbar1.get_xaxis().set_visible(False)
    axbar1.set_xlim(0., NChannels)
    axbar1.axvline(0, color=ChanColors[0])
    axbar1.axvline(NChannels, color=ChanColors[1])
    axbar1.set_ylim(-ChanRanges[0],ChanRanges[0])
    axbar1.axhline(0., color='k', linestyle='-', lw=2, alpha=0.5)
    axbar2.set_ylim(-ChanRanges[1], ChanRanges[1])
    axbar1.set_ylabel('Chan A (V)', color=ChanColors[0])
    axbar2.set_ylabel('Chan B (V)', color=ChanColors[1])
    # Voltage in Text format
    axes.append(plt.subplot2grid((7,1),(0,0)) )
    axtxt=axes[3]
    axtxt.set_frame_on(False)
    axtxt.get_xaxis().set_visible(False)
    axtxt.get_yaxis().set_visible(False)
    axtxt.set_title('Picoscope as Voltmeter', size='xx-large')

    return fig, axes, axbar1, axbar2
# -- end def grVMeterIni

  def animVMeterIni():
  # initialize objects to be animated
    global bgraph1, bgraph2, graphsVM, animtxtVM
    # a bar graph for the actual voltages
#    bgraph = axes[0].bar(ind, np.zeros(NChannels), bwidth,
#                           align='center', color='grey', alpha=0.5)
    bgraph1, = axbar1.bar(ind[0], 0. , bwidth,
                           align='center', color=ChanColors[0], alpha=0.5) 
    bgraph2, = axbar2.bar(ind[1], 0. , bwidth,
                           align='center', color=ChanColors[1], alpha=0.5) 

    # history graphs
    graphsVM=()
    for i, C in enumerate(picoChannels):
      g,= axesVM[i].plot(ix, np.zeros(Npoints), color=ChanColors[i])
      graphsVM += (g,)
    animtxtVM = axesVM[3].text(0.05, 0.05 , ' ',
                transform=axesVM[3].transAxes,
                size='large', color='darkblue')
#    return bgraph + graphsVM + (animtxt,)
    return (bgraph1,) + (bgraph2,) + graphsVM + (animtxtVM,)  
# -- end grVMeterIni()

  def animVMeter( (n, evTime, evData) ):
    k=n%Npoints

    txt_t='Time  %.1fs' %(evTime-t0)            
    txt=[]
    for i, C in enumerate(picoChannels):
      V[i] = evData[i].mean()
      Vhist[i, k] = V[i]
      stdV[i] = evData[i].std()
      stdVhist[i, k] = stdV[i]
      # update history graph
      if n>1: # !!! fix to avoid permanent display of first object in blit mode
        graphsVM[i].set_data(ix,
          np.concatenate((Vhist[i, k+1:], Vhist[i, :k+1]), axis=0) )
      else:
        graphsVM[i].set_data(ix,np.zeros(Npoints))
      txt.append('Chan. %s:   %.3gV +/-%.2g' % (C, Vhist[i,k], stdVhist[i,k]) )
    # update bar chart
#    for r, v in zip(bgraph, V):
#        r.set_height(v)
    if n>1: # !!! fix to avoid permanent display of first object in blit mode
      bgraph1.set_height(V[0])
      bgraph2.set_height(V[1])
    else:  
      bgraph1.set_height(0.)
      bgraph2.set_height(0.)
    animtxtVM.set_text(txt_t + '\n' + txt[0] + '\n' + txt[1])
#
    return (bgraph1,) + (bgraph2,) + graphsVM + (animtxtVM,)
#- -end def animVMeter
#-end def VMeter

                
#def Osci():
  # Oscilloscope: display channel readings in time domain

  def grOsciIni():
# set up a figure to plot samplings from Picoscope
  # needs revision if more than 2 Channels present
    fig=plt.figure("Oscilloscope", figsize=(6., 4.) )
    fig.subplots_adjust(left=0.13, bottom=0.125, right=0.87, top=0.925,
                    wspace=None, hspace=.25)
    axes=[]
# channel A
    axes.append(fig.add_subplot(1,1,1, facecolor='ivory'))
    axes[0].set_ylim(-ChanRanges[0],ChanRanges[0])
    axes[0].grid(True)
    axes[0].set_ylabel("Chan. A     Voltage (V)",
                     size='x-large',color=ChanColors[0])
    axes[0].tick_params(axis='y', colors=ChanColors[0])
# channel B
    if len(picoChannels)>1:
      axes.append(axes[0].twinx())
      axes[1].set_ylim(-ChanRanges[1],ChanRanges[1])
      axes[1].set_ylabel("Chan. B     Voltage (V)",
                     size='x-large',color=ChanColors[1])
      axes[1].tick_params(axis='y', colors=ChanColors[1])

  # time base
    axes[0].set_xlabel("Time (ms)", size='x-large') 

    trgidx=picoChannels.index(trgChan)
    trgax=axes[trgidx]
    trgcol=ChanColors[trgidx]

    axes[0].set_title("Trigger: %s, %.3gV %s" % (trgChan, trgThr, trgTyp),
                color=trgcol,
                fontstyle='italic', fontname='arial', family='monospace',
                horizontalalignment='right')
    axes[0].axhline(0., color='k', linestyle='-.', lw=2, alpha=0.5)
    trgax.axhline(trgThr, color=trgcol, linestyle='--')
    trgax.axvline(0., color=trgcol, linestyle='--')

    return fig, axes
# -- end def grOsciIni

  def animOsciIni():
  # initialize objects to be animated
    global graphsOs, animtxtOs
    graphsOs = ()
    for i, C in enumerate(picoChannels):
      g,= axesOs[i].plot(samplingTimes, np.zeros(NSamples), color=ChanColors[i])
      graphsOs += (g,)
    animtxtOs = axesOs[0].text(0.65, 0.95, ' ', transform=axesOs[0].transAxes,
                   backgroundcolor='white', alpha=0.5)
    return graphsOs + (animtxtOs,)
  
  def animOsci( (n, evTime, evData) ):
    global n0 
    if n==1: n0=0
    if n>2:    # !!! fix to avoid permanent display of first line in blit mode
      for i, C in enumerate(picoChannels):
        graphsOs[i].set_data(samplingTimes, evData[i])
    else:
      for i, C in enumerate(picoChannels):
        graphsOs[i].set_data([],[])

# display rate and life time
    if n-n0 == 50:
      txt='rate: %.3gHz  life: %.0f%%' % (BM.readrate, BM.lifefrac)
      animtxtOs.set_text(txt)
      n0=n
    return graphsOs + (animtxtOs,)
# -end animOsci
  
# - control part for graphical Instruments()
  anims=[]
  if mode==0 or mode==2:
# Voltmeter
    Wtime=500.    # time in ms between samplings
    Npoints = 120  # number of points for history
    ix=np.linspace(-Npoints+1, 0, Npoints) # history plot
    bwidth=0.5
    ind = bwidth + np.arange(NChannels) # bar position in bargraph for voltages
    V=np.empty(NChannels)
    stdV=np.empty(NChannels)
    Vhist=np.zeros( [NChannels, Npoints] )
    stdVhist=np.zeros( [NChannels, Npoints] )

    t0=time.time()
    if verbose>0: print(' -> Voltmeter starting')
    figVM, axesVM, axbar1, axbar2 = grVMeterIni()

    anims.append(anim.FuncAnimation(figVM, animVMeter, yieldVMEvent,
                         interval=Wtime, init_func=animVMeterIni,
                         blit=True, fargs=None, repeat=True, save_count=None) )
   # save_count=None is a (temporary) workaround to fix memory leak in animate

  if mode==1 or mode==2:  
    if verbose>0: print(' -> Oscilloscope starting')
    figOs, axesOs = grOsciIni()

    anims.append(anim.FuncAnimation(figOs, animOsci, yieldOsEvent, interval=50,
                         init_func=animOsciIni, blit=True,
                         fargs=None, repeat=True, save_count=None))
   # save_count=None is a (temporary) workaround to fix memory leak in animate

  try:
    plt.show()
  except: 
    print ('matplotlib animate exiting ...')
