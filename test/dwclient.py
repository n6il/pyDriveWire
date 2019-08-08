import sys
sys.path.append('..')
import time
from struct import *
from ctypes import *
import traceback

from dwconstants import *

import dwsocket

debug = False
channel_open = False


def openChannel(s, channel):
   # open a vserial
   # data = OP_SERINIT
   # data += chr(channel)
   # s.write(data)
   data = OP_SERSETSTAT
   data += chr(channel)
   data += SS_Open
   s.write(data)
   if debug:
      print "channel %s open" % channel
   channel_open = True

def closeChannel(s, channel):
   # close
   if debug:
      print "closing channel: %s" % channel
   data = OP_SERSETSTAT
   data += chr(channel)
   data += SS_Close
   s.write(data)
   # data = OP_SERTERM
   # data += chr(channel)
   # s.write(data)
   getStatus(s, channel)
   channel_open = False

def getStatus(s, channel):
   # get status
   s.write(OP_SERREAD)
   r = [ord(c) for c in s.read(2)]
   if debug:
       print "channel status: %s" % r
   return r

def writeChannel(s, channel, data):
   for c in data:
      # dd = OP_SERWRITE
      # dd += chr(channel)
      dd = eval("OP_FASTWRITE%d" % channel)
      dd += c
      s.write(dd)
   if debug:
      print "write: ch=%d %s" % (channel, data)

def readChannel(s, channel, wait=False):
   out=""
   while True:
      code,sdata = getStatus(s, channel)
      if code == 0:
         if wait:
             continue
         else:
             break
      elif code == 16:
          channel_open = False
      elif code <16:
         out += sdata
      elif code>16 and sdata > 0:
         data = OP_SERREADM
         data += chr(channel)
         data += chr(sdata)
         s.write(data)
         out += s.read(sdata)
      wait=False
   return out

s = dwsocket.DWSocket(port=65504)
s.debug = True
s.connect()
channel = 2
while True:
   print "dwclient> ",
   command = raw_input()
   if command.startswith('quit'):
      break
   elif command.startswith('status'):
       getStatus(s, channel)
       continue
   elif command.startswith('close'):
       closeChannel(s, channel)
       continue
   if not channel_open:
       openChannel(s, channel)
   getStatus(s, channel)
   writeChannel(s, channel, command+'\r')
   print readChannel(s, channel, True)
   if not channel_open:
       closeChannel(s, channel)
closeChannel(s, channel)
getStatus(s, channel)
