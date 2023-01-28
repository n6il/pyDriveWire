#!/usr/bin/python
import socket
import threading
import sys
sys.path.append("..")
from dwconstants import *
from dwutil import *
from struct import *
from ctypes import *
from dwutil import *

import time

if len(sys.argv) < 2:
   print('Usage: %s <audiofile>' % sys.argv[0])
   exit(1)
s = socket.socket( socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

addr = '127.0.0.1'
port = 65504
cs = socket.create_connection((addr, port))
print "connection to : %s:%s" % (addr,port)

fn = sys.argv[1]
cs.send(OP_PLAYSOUND)
cs.send(chr(len(fn)))
cs.send(fn)
data = cs.recv(1)
print("Result: %d" % ord(data))
assert(ord(data) == 0x00)

