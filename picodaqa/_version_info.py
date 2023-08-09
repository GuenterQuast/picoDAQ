'''
.. module:: _version_info
   :platform: >=3.6
   :synopsis: Version 1.1.1 of picodaq, rel. May 23

.. moduleauthor:: Guenter Quast <guenter.quast@online.de>
'''

major = 1
minor = 1
revision = 1

def _get_version_tuple():
  '''
  version as a tuple
  '''
  return (major, minor, revision)

def _get_version_string():
  '''
  version as a string
  '''
  return "%d.%d.%d" % _get_version_tuple()

