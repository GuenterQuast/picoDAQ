'''read a json file (with comments marked with '#')'''

from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
import json

def read_config(jsonfile):
# -- helper function to filter input lines
  def filter_lines(f, cc='#'):
    """ remove charcters after comment character cc from file  
      Args:
        * file f:  file 
        * char cc:   comment character
      Yields:
        * string 
    """
    jtxt=''
    while True:
      line=f.readline()
      if (not line): return jtxt # EOF
      if cc in line:
        line=line.split(cc)[0] # ignore everything after comment character    
        if (not line): continue # ignore comment lines
      if (not line.isspace()):  # ignore empty lines
        jtxt += line        
#   -- end filter_lines
  jsontxt = filter_lines(jsonfile)
  return json.loads(jsontxt) 

