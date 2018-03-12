from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import time, numpy as np

# - - - - some examples of consumers connected to BufferManager- - - - 

def obligConsumer(BM):
  '''
    test readout speed: do nothing, just request data from buffer manager

      - an example of an obligatory consumer, sees all data
        (i.e. data acquisition is halted when no data is requested)
    
    for reasons of speed, only a pointer to the event buffer is returned
  '''

  if not BM.ACTIVE.value: sys.exit(1)
# register with Buffer Manager
  myId = BM.BMregister()
  mode = 0    # obligatory consumer, request pointer to Buffer

  evcnt=0
  while BM.ACTIVE.value:
    e = BM.getEvent(myId, mode=mode)
    if e != None:
      evNr, evtime, evData = e
      evcnt+=1
      print('*==* obligConsumer: event Nr %i, %i events seen'%(evNr,evcnt))

#    introduce random wait time to mimick processing activity
    time.sleep(-0.25 * np.log(np.random.uniform(0.,1.)) )
  return
#-end def obligComsumer

def randConsumer(BM):
  '''
    test readout speed: 
      does nothing except requesting random data samples from buffer manager
  '''

  if not BM.ACTIVE.value: sys.exit(1)
  # register with Buffer Manager
  myId = BM.BMregister()
  mode = 1    # random consumer, request event copy

  evcnt=0
  while BM.ACTIVE.value:
    e = BM.getEvent(myId, mode=mode)
    if e != None:
      evNr, evtime, evData = e 
      evcnt+=1
      print('*==* randConsumer: event Nr %i, %i events seen'%(evNr,evcnt))
# introduce random wait time to mimick processing activity
    time.sleep(np.random.randint(100,1000)/1000.)
# - end def randConsumer()
  return
#
def subprocConsumer(Q):
  '''
    test consumer in subprocess 
      reads event data from multiprocessing.Queue()
  '''    
  if not BM.ACTIVE.value: sys.exit(1)

  cnt = 0  
  try:         
    while True:
      evN, evT, evBuf = Q.get()
      cnt += 1
      print('*==* mpQ: got event %i'%(evN) )
      if cnt <= 3:
        print('     event data \n', evBuf)        
      time.sleep(1.)
  except:
    print('subprocConsumer: signal recieved, ending')

