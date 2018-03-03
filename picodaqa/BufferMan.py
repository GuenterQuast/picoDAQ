'''
.. module BufferMan of picoDAQ

.. author: Guenter Quast <guenter.quast@online.de>
'''
#
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

# - class BufferMan
import numpy as np, sys, time, threading
from collections import deque

from multiprocessing import Queue, Process, Array
from multiprocessing.sharedctypes import RawValue, RawArray

from .mpLogWin import * 
from .mpBufManInfo import *
from .mpOsci import * 

  
class BufferMan(object):
  '''
  A simple Buffer Manager

  Calls rawDAWproducer() to receive data from hardware device
  and stores them in the classes buffer space. Data are served
  from buffer to obligatory consumers (i.e. data qcquisition
  is paused until all consumcers are done) and random consumers
  (receive an event copy, data acquisition continues regardless
  of the consumers' progress)
  '''

  def __init__(self, BMdict, DevConf):
    '''Args:  configuration dictionary
              Device Class             
    '''
    self.DevConf = DevConf  
    self.NChannels = DevConf.NChannels # number of channels in use
    self.NSamples = DevConf.NSamples   # number of samples 
    self.TSampling = DevConf.TSampling # sampling interval
    # function collecting data from hardware device
    self.rawDAQproducer = DevConf.acquireData 

    if "NBuffers" in BMdict: 
      self.NBuffers = BMdict["NBuffers"] # number of buffers
    else:
      self.NBuffers= 16
    if "BMmodules" in BMdict: 
      self.BMmodules = BMdict["BMmodules"] # display modules to start
    else:
      self.BMmodules = ["mpBufInfo"]
    if "LogFile" in BMdict:
      self.LogFile = BMdict["LogFile"]
    else:
      self.LogFile = None
    self.flog = None    # file not yet open
    if "verbose" in BMdict: 
      self.verbose = BMdict["verbose"]
    else:
      self.verbose=1   # print (detailed) info if >0 
    if "logTime" in BMdict: 
      self.logTime = BMdict["logTime"] # display modules to start
    else:
      self.logTime = 60 # logging information once per 60 sec

  # set up data structure for BufferManager
    self.BMbuf = np.empty([self.NBuffers, self.NChannels, self.NSamples], 
          dtype=np.float32 )
    self.timeStamp = np.empty(self.NBuffers)
#(
# eventually use shared c-type memory (would need adjustmens in picoDevice) 
#    self.BMbuf = RaWArray('f', (self.NBuffers, self.NChannels, self.NSamples) )
#    self.timeStamp = RawArray('f', self.NBuffers )
#)
    self.ibufr = -1     # read index, used to synchronize with producer 

    self.procs=[] # list of sub-processes started by BufferMan

  # set up status 
    self.BMT0 = 0.
    self.ACTIVE = RawValue('b', 0) 
    self.RUNNING = RawValue('b', 0)

  # queues (collections.deque() for communication with threads
    self.prod_que = deque(maxlen=self.NBuffers) # acquireData <-> manageDataBuffer
    self.request_ques=[] # consumer request to manageDataBuffer
                # 0:  request event pointer, obligatory consumer
                # 1:  request event data, random consumer 
                # 2:  request event data, obligatoray consumer
    self.consumer_ques=[] # data from manageDataBuffer to consumer

  # multiprocessing Queues for data transfer to subprocesses
    self.mpQues = []
    self.BMInfoQue = None

  # producer statistics
    self.Ntrig = 0
    self.readrate = 0.
    self.lifefrac = 0.

    self.BMlock = threading.Lock() 
    self.logQ = None
    
  def acquireData(self):
    '''
     Procucer Thread
    
       - collects and stores data in buffers
       - provides all acquired data to manageDataBufer 
       - count number of events and calculate life time

       Arg: funtion handling data acquisition from device

     Communicates with consumer via collections.deque()

    '''
#    self.prlog('*==* BufMan:  !!! acquireData starting')
    self.Ntrig = 0    # count number of readings
    self.Ttrig = 0    # time of last event
    self.Tlife = 0.
    self.readrate = 0.
    self.lifefrac = 0.
    tlife = 0.

    ni = 0       # temporary variable
    ts = time.time()
  
    ibufw = -1   # buffer index
    while self.ACTIVE.value:
  # sample data from Picoscope handled by instance ps
      ibufw = (ibufw + 1) % self.NBuffers # next write buffer
      while ibufw==self.ibufr:  # wait for consumer done with this buffer
        if not self.ACTIVE.value: 
          if self.verbose: self.prlog ('*==* BufMan.acquireData()  ended')
          return
        time.sleep(0.001)
#
      while not self.RUNNING.value:   # wait for running status 
        if not self.ACTIVE.value: 
          if self.verbose: self.prlog('*==* BufMan.acquireData()  ended')
          return
        time.sleep(0.01)

# data acquisition from hardware
      e = self.rawDAQproducer(self.BMbuf[ibufw])
      if e == None: 
        if self.verbose: self.prlog('*==* BufMan.acquireData()  ended')
        return
      ttrg, tl = e
      tlife += tl
      ttrg -= self.BMT0
      self.Tlife += tl
      self.timeStamp[ibufw] = ttrg  # store time when data became ready
      self.Ttrig = ttrg
      self.Ntrig += 1
      self.prod_que.append( (self.Ntrig, ibufw) )
       
# wait for free buffer       
      while len(self.prod_que) == self.NBuffers:
        if not self.ACTIVE.value: 
          if self.verbose: self.prlog('*==* BufMan.acquireData()  ended')
          return
        time.sleep(0.001)
      
# calculate life time and read rate
      if (self.Ntrig - ni) == 10:
        dt = time.time()-ts
        ts += dt
        self.readrate = (self.Ntrig-ni)/dt
        self.lifefrac = (tlife/dt)*100.      
        tlife = 0.
        ni=self.Ntrig
    # --- end while  
    if self.verbose: self.prlog('*==* BufMan.acquireData()  ended')
    return
# -- end def acquireData


  def manageDataBuffer(self):
    '''main Consumer Thread 

       - request data from procuder (acquireData):
       - provide all events for analysis to "obligatory" consumers
       - provide subset of events to "random" consumers (picoVMeter, oscilloscope)

    '''
    t0=time.time()
    n0=0
    n=0
    while self.ACTIVE.value:
      while not len(self.prod_que): # wait for data in producer queue
        if not self.ACTIVE.value:
          if self.verbose: self.prlog('*==* BufMan ended')
          return
        time.sleep(0.001)
      evNr, self.ibufr = self.prod_que.popleft()

# !debug    self.prlog('ibufr=', self.ibufr,'request_ques',self.request_ques)

# check if other threads want data
      l_obligatory=[]
      if len(self.request_ques):
        for i, q in enumerate(self.request_ques):
          if len(q):
            req = q.popleft()
            if req==0:                          # return poiner to Buffer      
              self.consumer_ques[i].append( (evNr, self.ibufr) ) 
              l_obligatory.append(i)
            elif req==1:                               # return a copy of data
              evTime=self.timeStamp[self.ibufr]
              self.consumer_ques[i].append( (evNr, evTime, np.copy(self.BMbuf[self.ibufr]) ) )
            elif req==2:                   # return copy and mark as obligatory
              evTime=self.timeStamp[self.ibufr]
              self.consumer_ques[i].append( (evNr, evTime, np.copy(BMbuf[self.ibufr]) ) )
              l_obligatory.append(i)
            else:
              self.prlog('!=! manageDataBuffer: invalid request mode', req)
              sys.exit(1)
# check if other processes want data
      if len(self.mpQues):
        for Q in self.mpQues:
          if Q.empty(): # put an event in the Queue
            evTime=self.timeStamp[self.ibufr]
            Q.put( (evNr, evTime, np.copy(self.BMbuf[self.ibufr]) ) )

# wait until all obligatory consumers are done
      if len(l_obligatory):
        while self.ACTIVE.value:
          done = True
          for i in l_obligatory:
            if not len(self.request_ques[i]): done = False
          if done: break
          if not self.ACTIVE.value: 
            if self.verbose: self.prlog('*==* BufMan ended')
            return
          time.sleep(0.001)        
#  now signal to producer that all consumers are done with this event
      self.ibufr = -1

# print event rate
      n+=1
      if time.time()-t0 >= self.logTime:
        t0=time.time()
        if self.verbose:
          self.prlog('evt %i:  rate: %.3gHz   life: %.2f%%' %(n, 
              self.readrate, self.lifefrac))
        if(evNr != n): 
          self.prlog("!!! manageDataBuffer error: ncnt != Ntrig: %i, %i"%(n,
          evNr) )
#   - end while ACTIVE  
    if self.verbose: self.prlog('*==* BufMan ended')
    return
# -end def manageDataBuffer()

  def BMregister(self):
#    global request_ques, consumer_ques
    ''' 
    register a client to Buffer Manager

    Returns: client index
    '''

    self.BMlock.acquire() # my be called by many threads and needs protection ...  
    self.request_ques.append(deque(maxlen=1))
    self.consumer_ques.append(deque(maxlen=1))
    client_index=len(self.request_ques)-1
    self.BMlock.release()
  
    if self.verbose:
      self.prlog("*==* BMregister: new client id=%i" % client_index)
    return client_index

  def BMregister_mpQ(self):
#   multiprocessing Queue
    ''' 
    register a subprocess to Buffer Manager
    
    data will be transferred via a multiprocess Queue
    
    Returns: client index
             multiprocess Queue
    '''

    self.mpQues.append( Queue(1) )
    cid=len(self.mpQues)-1
  
    if self.verbose:
      self.prlog("*==* BMregister_mpQ: new subprocess client id=%i" % cid)
    return cid, self.mpQues[-1]

  def getEvent(self, client_index, mode=1):
    ''' 
    request event from Buffer Manager
 
      Arguments: 

        client_index client:  index as returned by BMregister()
        mode:   0: event pointer (olbigatory consumer)
                1: copy of event data (random consumer)
                2: copy of event (olbigatory consumer)

      Returns: 

        event data
    '''

    self.request_ques[client_index].append(mode)
    cq=self.consumer_ques[client_index]
    while not len(cq):
        if not self.ACTIVE.value: return
        time.sleep(0.01)
    #self.prlog('*==* getEvent: received event %i'%evNr)
    if mode !=0: # received copy of the event data
      return cq.popleft()
    else: # received pointer to event buffer
      evNr, ibr = cq.popleft()
      evTime = self.timeStamp[ibr]
      evData = self.BMbuf[ibr]
      return evNr, evTime, evData
#
  def start(self):
    if self.verbose > 1: 
      self.prlog('*==* BufferMan  starting acquisition threads')
    self.ACTIVE.value = True 
    thr_acquireData=threading.Thread(target=self.acquireData)
    thr_acquireData.daemon=True
    thr_acquireData.setName('acquireData')
    thr_acquireData.start()

    thr_manageDataBuffer=threading.Thread(target=self.manageDataBuffer)
    thr_manageDataBuffer.daemon=True
    thr_manageDataBuffer.setName('manageDataBuffer')
    thr_manageDataBuffer.start()

  # logging window for buffer manager
    self.logQ = Queue()
    self.procs.append(Process(name='LogWin', 
                        target = mpLogWin, args=(self.logQ, ) ) )
  # Buffer Info
    if 'mpBufInfo' in self.BMmodules: 
      maxBMrate = 100.
      BMIinterval = 1000.
      self.procs.append(Process(name='BufManInfo',
                   target = mpBufManInfo, 
                   args=(self.getBMInfoQue(), maxBMrate, BMIinterval) ) )
#                           BM InfoQue      max. rate  update interval
  # waveform display 
    if 'mpOsci' in self.BMmodules: 
      OScidx, OSmpQ = self.BMregister_mpQ()
      self.procs.append(Process(name='Osci',
                              target = mpOsci, 
                              args=(OSmpQ, self.DevConf, 50., 'event rate') ) )
#                                               interval
# start BufferMan background processes   
    for prc in self.procs:
#      prc.deamon = True
      prc.start()
      if self.verbose:
        print('      BufferMan: starting process ', prc.name, ' PID =', prc.pid)

  def run(self):
    if self.RUNNING.value:
      self.prlog('*==* BufferMan already running - do nothing')
      return

    tstart = time.time()
    if self.LogFile:
      datetime=time.strftime('%y%m%d-%H%M',time.gmtime(tstart))
      self.flog = open(self.LogFile + '_' + datetime + '.log', 'w')

    if self.verbose: self.prlog('*==* BufferMan T0')
    self.BMT0 = tstart
    if self.verbose: self.prlog('*==* BufferMan start running')

    self.RUNNING.value = True  

  def pause(self):
    if self.verbose: self.prlog('*==* BufferMan  pause')
    self.RUNNING.value = False  
    self.readrate = 0.

  def resume(self):
    if self.verbose: self.prlog('*==* BufferMan  resume')
    self.RUNNING.value = True
  
  def setverbose(self, vlevel):
    self.verbose = vlevel

  def getStatus(self):
    ''' Returns:
          tuple: Running status, number of events,
                 time of last event, rate, life fraction and buffer level
    '''
    bL = (len(self.prod_que)*100)/self.NBuffers
    stat = self.RUNNING.value
    return (stat, time.time()-self.BMT0, 
           self.Ntrig, self.Ttrig, self.Tlife, 
           self.readrate, self.lifefrac, bL) 

  def getBMInfoQue(self):
    '''multiprocessing Queue for status information 

       starts a background process to fill BMInfoQue

       Returns: multiprocess Queue
    '''

    self.BMInfoQue = Queue(1) 
  # start a background thread for reporting
    thr_BMInfoQ = threading.Thread(target=self.reportStatus,
                                   args=(self.BMInfoQue,)  )
    thr_BMInfoQ.daemon = True
    thr_BMInfoQ.setName('BMreportStatus')
    thr_BMInfoQ.start()

    if self.verbose:
      self.prlog("*==* BMInfoQue enabled")
    return self.BMInfoQue

  def reportStatus(self, Q):
    '''report Buffer manager staus to a multiprocessing Queue'''
    while self.ACTIVE.value:
      if Q is not None and Q.empty(): 
        Q.put( self.getStatus()) 
      time.sleep(0.1)

  def setLogQ(self, Q):
    '''set a Queue for log messages'''
    self.logQ = Q

  def prlog(self, m):
    ''' send a Message, to screen or to LogQ'''
    t = time.time() - self.BMT0 # add time stamp to message
    s = '%.2f '%(t) + m  
    if self.logQ is None:
      print(s)
    else:
      self.logQ.put(s)
    if self.flog:
      print(s, file = self.flog)

  def print_summary(self):
    datetime=time.strftime('%y%m%d-%H%M',time.gmtime(self.BMT0))
    if not self.flog:
      self.flog = open('BMsummary_' + datetime+'.sum', 'w')
    print('Run Summary: started ' + datetime, file=self.flog )
    print('  Trun=%.1fs  Ntrig=%i  Tlife=%.1fs\n'\
        %(time.time()-self.BMT0, self.Ntrig, self.Tlife), file=self.flog )
    self.flog.close()

  def end(self):
    self.pause()
    if self.verbose: 
      self.prlog('*==* BufferMan ending')
      print('*==* BufferMan ending')
      print('  Run Summary: Trun=%.1fs  Ntrig=%i  Tlife=%.1fs\n'\
        %(time.time()-self.BMT0, self.Ntrig, self.Tlife) )
    self.print_summary()
    self.ACTIVE.value = False 
    time.sleep(0.3)
  # stop all sub-processes
    for prc in self.procs:
      if self.verbose: print('    BufferMan: terminating '+prc.name)
      prc.terminate()
    time.sleep(0.3)

  def __del__(self):
    self.RUNNING.value = False
    self.ACTIVE.value  = False
# - end class BufferMan
