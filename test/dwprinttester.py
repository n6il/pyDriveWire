import sys
sys.path.append('..')
from dwconstants import *
import dwlib
import socket

def dwPrint(s, data, debug=False):
   for c in data:
      dd = OP_PRINT
      dd += c
      s.send(dd)
   s.send(OP_PRINTFLUSH)

   if debug:
      print("printed data\n")
      print(dwlib.canonicalize(data))

dws = socket.create_connection(('localhost', 65504))

with open(__file__) as f:
    data = f.read()
    dwPrint(dws, data, debug=True)
    dws.close()

# vim: ts=4 sw=4 sts=4 expandtab
