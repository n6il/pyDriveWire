import threading
import Queue
from threading import Lock
import copy
from dwcommand import DWParser
import time
from dwlib import canonicalize
from dwio import DWIO
from dwsocket import *

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
	def __init__(self, debug=False):
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
		self.debug = debug

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

class DWVModem2(DWChannel):
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
			

class DWVModem(DWIO):
	def __init__(self, server, channel, conn=None, debug=False):
		print "DWVModem __init__"
		DWIO.__init__(self, threaded=False)
		self.server=server
		self.channel=channel
		self.conn=conn
		self.inbound=False
		if self.conn:
			self.inbound=True
		self.debug = debug
		self.online = False
		self.wbuf = ''
		self.parser = DWParser(server)
		self.connected = True
		self.cq = Queue.Queue()
		self.cmdThread = threading.Thread(target=self._cmdWorker)
		self.cmdThread.daemon = True
		#self.cmdThread.start()
		self.eatTwo = False
		self.listeners = []
		self.echo = False
		self.cmdAutoClose = True
		

	def _acceptCb(self, conn):
		print "%s: accpet callback called" % self
		n = self.server.registerConn(conn)
		r = "%s %s %s" % (n, conn.port, conn.addr[0])
		reply = r + "\r" #+ r + "\r\n"
		if self.debug:
			print "reply: (%s)" % reply
		self.rq.put(reply)
		self.rb.add(len(reply))
	
	def _cmdWorker(self):
			#while True:
			if self.cq.empty():
				return
			cmd = self.cq.get(True)
			if self.debug:
				print "parser",cmd
			res = self.parser.parse(cmd)
			exact = False
			reply = "0 OK\r"
			if isinstance(res, str):
				if res.startswith("FAIL") or res.startswith("ERROR"):
					reply = res
				else:
					reply += res
				if self.cmdAutoClose and not self.online:
					self.connected = False
			elif isinstance(res, dict):
				for k,v in res.items():
					if isinstance(v, str):
						v = "'%s'" % v
					e = '%s=%s' % (k,v)
					if self.debug:
						print(e)
					exec(e)
			elif isinstance(res, DWSocketListener):
				self.online = True
				self.connected = True
				if self.debug:
					print "%s: register callback: %s" % (res, self._acceptCb)
				res.registerCb(self._acceptCb)
				res.at.start()
				self.listeners.append(res)	
				r = "OK listening on port %s" % res.port
				exact = True
				reply = r + "\r" #+ r + "\r\n"
			elif isinstance(res, DWIO):
				self.online = True
				self.conn = res
				b = self.conn.binding
				if b:
					reply = "OK attaching to connection %s\r" % (b)
				else:
					r = "OK connected to %s:%s" % (self.conn.host, self.conn.port)
					reply = r + "\n" + r + "\r\n"
					#self.eatTwo = True
				self.conn.run()
				exact = True
			# if self.online and not exact:
			if not exact:
				reply = '\r\n' + reply + '\r\n'
			if self.debug:
				print "reply: (%s)" % reply
			self.rb.add(len(reply))
			self.rq.put(reply)
			#while reply:
			#	self.rq.put(reply[:214])
			#	reply = reply[214:]
			#if isinstance(res, str):
		
			#elif res:
			#	res = "0 OK\r"+res#+'\r\n'
			#	print "res",res
			#	self.rq.put(res)
			#	self.rb.add(len(res))
			#	self.connected = False

	def write(self, data, ifs='\r'):
		if self.debug:
			print "ch: write:",canonicalize(data)
		wdata = ''
		w=0
		pos=-1
		#print "dwio read %d" % rlen
		#if not self.wt.is_alive():
		#	# Start the background reader thread only
		#	# when someone asks to start reading from it
		#	self.wt.start()

		if not self.eatTwo and self.online and self.conn:
			if self.wbuf:
				w += self.conn.write(self.wbuf)
				self.wbuf = ''
			w +=  self.conn.write(data)
		else:
			if self.echo:
				self.rq.put(data)
				self.rb.add(len(data))
			self.wbuf += data
			pos = self.wbuf.find(ifs)
			if pos < 0:
				w += len(data)
			#while pos >= 0:
			else:
				
				if self.eatTwo:
					if self.debug:
						print "ch: eating: %s" % canonicalize(self.wbuf[:pos+1])
				if self.echo:
					self.rq.put("\r")
					self.rb.add(1)
				wdata = self.wbuf[:pos]
				self.wbuf = self.wbuf[pos+1:]
				w += pos + 1	
				if self.debug:
					print "wdata=(%s) wbuf=(%s)" % (wdata, self.wbuf)
				if self.eatTwo:
					self.eatTwo=False
					
				else:
					self.cq.put(wdata)
				#self._cmdWorker()
				#print "parser",wdata
				#res = self.parser.parse(wdata)
				#if isinstance(res, DWIO):
				#	self.conn = res
				#elif res:
				#	res = "0 OK\r"+res#+'\r\n'
				#	print "res",res
				#	self.rq.put(res)
				#	self.rb.add(len(res))
				#	self.connected = False
				#pos = self.wbuf.find(ifs)

			#pos = data.find(ifs)
			#if pos >= 0:
			#	wdata = self.wbuf + data[:pos]
			#	self.wbuf = data[pos+1:]
			#	w = pos + 1
			#if wdata:
			#	res = self.parser.parse(wdata)
			#	if isinstance(res, DWIO):
			#		self.conn = res
			#	elif res:
			#		self.rq.put(res)
			#		self.rb.add(len(res))
			#else:
			#	self.wbuf += data
			#	w = len(data)
		return w

	#def _readHandler(self):
	def read(self, rlen=None):
		d = ''
		if self._outWaiting()>0:
			d +=  DWIO.read(self, rlen)
			#d += self.rq.get()
			#self.rb.sub(len(d))
			if d:
				if self.debug:
					print "ch:i: read:",canonicalize(d)
		#elif self.connected == False:
		#	self.rb.close()
		#elif self.conn and self.conn.outWaiting()>0:
		elif self.conn:
			d += self.conn.read(rlen)
			if d:
				if self.debug:
					print "ch:c: read:",canonicalize(d)
		#print "d: (%s)" % d
		return d

	def outWaiting(self):
		d = self._outWaiting()
		if d == 0 and self.connected == False:
			if self.debug:
				print "channel closing"
			self.rb.close()
		#if not self.conn:
		d=self._outWaiting()
		if self.debug:
			print "ch:%d ow:i=%d" % (ord(self.channel), d)
		#if d>=0 and self.conn:
		if d==0 and self.conn:
		#else:
			d = self.conn.outWaiting()
			if self.debug:
				print "ch:%d ow:c=%d" % (ord(self.channel), d)
			if d <= 0 and not self.conn.isConnected():
				self.rb.close()
				self.conn = None
				self.online = False
				self.connected = False
		return d

	def _close(self):
		if self.conn:
			self.conn.close()
		for c in self.listeners:
			c.close()
		self.rb.close()
		self.conn = None
		self.online = False
		self.connected = False
