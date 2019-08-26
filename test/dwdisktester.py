#!/usr/bin/python
import socket
import threading
import sys
sys.path.append("..")
from dwconstants import *
from dwutil import *
from struct import *
from ctypes import *

import time

def worker(cs):
   try:
      while True:
         data = cs.recv(192)
         dl = len(data)
         print dl
         if dl>0:
            written=0
            while written<dl:
               written +=cs.send(data[written:])
         else:
            print "Connection dropped."
            break
   finally:
      print "Listening again..."

if len(sys.argv) < 2:
   exit(1)
s = socket.socket( socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
listen = False
if listen:
   print("Listening on port 65504...")
   s.bind(('0.0.0.0', 65504))
   s.listen(0)
if True:
   if listen:
      (cs, addr) = s.accept()
      print "Accepted connection: %s" % str(addr)
   else:
      #addr = "172.16.1.89"
      #addr = "192.168.4.1"
      addr = '127.0.0.1'
      port = 65504
      cs = socket.create_connection((addr, port))
      print "connection to : %s:%s" % (addr,port)

   print("s")
   cs.send(OP_DWINIT)
   cs.send('A')
   data = cs.recv(1)
   print("r")
   assert(ord(data) == 0xff)
   disk = 0
   for fileName in sys.argv[1:]:
      print ("Checking: %s" % fileName)
      f = open(fileName)
      rc = E_OK
      lsn = 0
      while rc == E_OK:
         fd = f.read(256)
         fc = dwCrc16(fd)
         # send command
         cs.send(OP_READEX)
         # send disk
         cs.send(pack(">I",disk)[-1:])
         # send lsn
         cs.send(pack(">I",lsn)[-3:])
         # Read the data
         data = cs.recv(256)
         sc = dwCrc16(data)
         # Write the CRC
         cs.send(sc)
         # Get the RC
         rc = ord(cs.recv(1))
         print("lsn=%d fc=%s sc=%s" % (lsn, hex(unpack(">H", fc)[0]), hex(unpack(">H", sc)[0])))
         assert(fc == sc)
         print("OP_READEX lsn %d len %d %d" % (lsn, len(data), rc))
         #msg = "%d ..." % lsn
         #msg+'\b'*len(msg),
         #print ".",
         lsn += 1
      
      print("\nCompared %d sectors rc %d" % (lsn, rc))
      assert(rc in [E_OK, E_EOF])
      f.close()
