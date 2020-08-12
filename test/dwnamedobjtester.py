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
   exit(1)
s = socket.socket( socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

addr = '127.0.0.1'
port = 65504
cs = socket.create_connection((addr, port))
print "connection to : %s:%s" % (addr,port)

fn = sys.argv[1]
cs.send(OP_NAMEOBJ_CREATE)
cs.send(chr(len(fn)))
cs.send(fn)
data = cs.recv(1)
assert(ord(data) == 0xff)

cs.send(OP_WRITE)
cs.send('\xff')
cs.send('\x00\x00\x00')
dataA = 'A' * 256
crcA = dwCrc16(dataA)
cs.send(dataA)
cs.send(crcA)
data = cs.recv(1)
assert(ord(data) == 0x00)

cs.send(OP_TIME)
data = cs.recv(6)
cs.send(OP_NOP)

fn = sys.argv[1]
cs.send(OP_NAMEOBJ_MOUNT)
cs.send(chr(len(fn)))
cs.send(fn)
data = cs.recv(1)
assert(ord(data) == 0xff)

cs.send(OP_READEX)
cs.send('\xff')
cs.send('\x00\x00\x00')
data = cs.recv(256)
mycrc = dwCrc16(data)
cs.send(mycrc)
rc = cs.recv(1)
assert(ord(rc) == 0)
assert(mycrc == crcA)
assert(data == dataA)

time.sleep(int(sys.argv[2]))
cs.send(OP_TIME)
data = cs.recv(6)
cs.send(OP_NOP)


