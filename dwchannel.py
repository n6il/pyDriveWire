from threading import Lock
import copy
from dwcommand import DWParser
import time

# DWChannel is a bi-directional pipe between the client and the service
# Client interface: read,write,inWaiting,outWaiting
#   The client reads from outbuf and writes to inbuf
#   The client may poll by using inWaiting and outWaiting
#   If the cleint has registered outCb it is notified when the service has put new data
# Service interface: get, put, inCb, outCb
#   The service reads from inbuf and writes to outbuf
#   The service must register inCb
#   The service is notified via inCb that the client has written new data
class DWChannel:
	def __init__(self):
		self.connected = True
		self.inbuf = ''
		self.inmutex = Lock()
		self.inCb = None
		self.outbuf = ''
		self.outmutex = Lock()
		self.outCb = None
		self.lineMode = True
		self.lineChr = chr(0x0d)
		self.outsize = 255

	def inWaiting(self):
		self.inmutex.acquire()
		l = len(self.inbuf)
		self.inmutex.release()
		return l

	def outWaiting(self):
		self.outmutex.acquire()
		l = len(self.outbuf)
		self.outmutex.release()
		if l == 0 and not self.connected:
			l=-1
		return min(self.outsize, l)

	# read data from outbuf
	def read(self, num=None):
		self.outmutex.acquire()
		if num==None:
			num = min(len(self.outbuf), self.outsize)
		d = copy.copy(self.outbuf[:num])
		self.outbuf = self.outbuf[num:]
		self.outmutex.release()
		return d

	# write data to inbuf
	def write(self, data):
		self.inmutex.acquire()
		self.inbuf += data
		self.inmutex.release()
		if self.inCb:
			notify = True
			l = len(data)
			if self.lineMode:
				i = self.inbuf.find(self.lineChr)
				if i >=0:
					l=i
				else:
					notify = False
			if notify:
				self.inCb(l)
		return len(data)

	# read data from inbuf
	def get(self, num=None):
		self.inmutex.acquire()
		if num==None:
			num = len(self.inbuf)
		d = copy.copy(self.inbuf)
		self.outbuf = self.inbuf[num:]
		self.inmutex.release()
		return d

	# write data to outbuf
	def put(self, data):
		self.outmutex.acquire()
		self.outbuf += data
		self.outmutex.release()
		if self.outCb:
			self.outCb.notify(len(data))
		return len(data)

class DWSerialChannel(DWChannel):
	def __init__(self, server, conn=None):
		DWChannel.__init__(self)
		self.commandMode = True
		self.dataMode = False
		self.inCb = self.notify
		self.parser = DWParser(server)
		self.conn = conn

	def notify(self, num):
		# Sending us a line
		data = self.get(num).strip()
		print "notify: %s" % data
		res = self.parser.parse(data)
		if res:
			self.put(str(res))
			#while self.outWaiting():
			#	time.sleep(1)
			self.connected=False
			
		
