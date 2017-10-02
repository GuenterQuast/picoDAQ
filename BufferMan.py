'''
.. module BufferMan of picoDAQ

.. author: Guenter Quast <guenter.quast@online.de>
'''
#
# - class BufferMan
import numpy as np, time, threading
from collections import deque
  
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

  def __init__(self, NBuffers, NChannels, NSamples, rawDAQproducer):
    ''' data structure for BufferManager '''
    self.NBuffers = NBuffers
    self.NChannels = NChannels
    self.NSamples = NSamples

  # function collecting data from hardware device
    self.rawDAQproducer = rawDAQproducer  

  # set up event buffer
    self.BMbuf = np.empty([NBuffers, NChannels, NSamples], dtype=np.float32 )
    self.timeStamp = np.empty(NBuffers)
    self.ibufr = -1     # read index, used to synchronize with producer 

  # queues (collections.deque() for communication with threads
    self.prod_que = deque(maxlen=NBuffers) # acquireData <-> manageDataBuffer
    self.request_ques=[] # consumer request to manageDataBuffer
                # 0:  request event pointer, obligatory consumer
                # 1:  request event data, random consumer 
                # 2:  request event data, obligatoray consumer
    self.consumer_ques=[] # data from manageDataBuffer to consumer

  # producer statistics
    self.Ntrig = 0
    self.readrate = 0.
    self.lifefrac = 0.

    self.BMlock = threading.Lock() 

    self.verbose = 1
    
  def acquireData(self):
    '''
     Procucer Thread
    
       - collects and stores data in buffers
       - provides all acquired data to exactly one consumer, manageDataBufer 

       Arg: funtion handling data acquisition from device

     Communicates with consumer via collections.deque()

    '''
#    print ('       !!! acquireData starting')
    self.Ntrig = 0    # count number of readings
    self.readrate = 0.
    self.lifefrac = 0.
    tlife = 0.

    ni = 0       # temporary variable
    ts = time.time()
  
    ibufw = -1   # buffer index
    while self.RUNNING:
  # sample data from Picoscope handled by instance ps
      ibufw = (ibufw + 1) % self.NBuffers # next write buffer
      while ibufw==self.ibufr:  # wait for consumer done with this buffer
        if not self.RUNNING: return
        time.sleep(0.001)
#
# data acquisition from hardware
      ttrg, tl = self.rawDAQproducer(self.BMbuf[ibufw])
      tlife += tl
      self.timeStamp[ibufw] = ttrg  # store time when data became ready
      self.Ntrig += 1
      self.prod_que.append( (self.Ntrig, ibufw) )
       
# wait for free buffer       
      while len(self.prod_que) == self.NBuffers:
        if not self.RUNNING: return
        time.sleep(0.001)
      
# calculate life time and read rate
      if (self.Ntrig - ni) == 100:
        dt = time.time()-ts
        self.readrate = (self.Ntrig-ni)/dt
        self.lifefrac = (tlife/dt)*100.      
        ts += dt
        tlife = 0.
        ni=self.Ntrig
    # --- end while  
    print ('          !!! acquireData()  ended')
    return 0
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
    while True:
      while not len(self.prod_que): # wait for data in producer queue
        time.sleep(0.001)
      evNr, self.ibufr = self.prod_que.popleft()

# !debug    print('ibufr=', self.ibufr,'request_ques',self.request_ques)

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
              print('!!! manageDataBuffer: invalid request mode', req)
              exit(1)

# wait until all obligatory consumers are done
      if len(l_obligatory):
        while True:
          done = True
          for i in l_obligatory:
            if not len(self.request_ques[i]): done = False
          if done: break
          time.sleep(0.001)        
#  now signal to producer that all consumers are done with this event
      self.ibufr = -1

# print event rate
      n+=1
      if time.time()-t0 >= 10:
        if self.verbose:
          print('evt %i:  rate: %.3gHz   life: %.2f%%' % (n, self.readrate, self.lifefrac))
        if(evNr != n): print ("!!! ncnt != Ntrig: %i, %i"%(n,evNr) )
        t0=time.time()
#   - end while True  
# -end def manageDataBuffer()

  def BMregister(self):
#    global request_ques, consumer_ques
    ''' 
    register a client to in Buffer Manager

    Returns: client index
    '''

    self.BMlock.acquire() # my be called by many threads and needs protection ...  
    self.request_ques.append(deque(maxlen=1))
    self.consumer_ques.append(deque(maxlen=1))
    client_index=len(self.request_ques)-1
    self.BMlock.release()
  
    if self.verbose:
      print("*==* BMregister: new client id=%i" % client_index)
    return client_index

  def BMgetEvent(self, client_index, mode=1):
    global request_ques, consumer_ques
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
        time.sleep(0.01)
  #print('*==* BMgetEvent: received event %i'%evNr)
    if mode !=0: # received copy of the event data
      return cq.popleft()
    else: # received pointer to event buffer
      evNr, ibr = cq.popleft()
      evTime = self.timeStamp[ibr]
      evData = self.BMbuf[ibr]
      return evNr, evTime, evData
#
  def run(self):
    self.RUNNING = True  
    thr_acquireData=threading.Thread(target=self.acquireData)
    thr_acquireData.daemon=True
    thr_acquireData.setName('aquireData')
    thr_acquireData.start()

    thr_manageDataBuffer=threading.Thread(target=self.manageDataBuffer)
    thr_manageDataBuffer.daemon=True
    thr_manageDataBuffer.setName('manageDataBuffer')
    thr_manageDataBuffer.start()

  def setverbose(self, vlevel):
    self.verbose = vlevel

  def __del__(self):
    self.RUNNING = False
# - end class BufferMan
