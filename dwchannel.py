import threading
import Queue
from threading import Lock
import copy
from dwcommand import DWParser
import time
from dwlib import canonicalize
from dwio import DWIO
from dwsocket import *


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
			reply = "0 OK command successful\r\n"
                        obj = None
                        msg = None
			if isinstance(res, dict):
				for k,v in res.items():
                                        if k=='obj':
                                            obj = v
                                        elif k=='msg':
                                            msg = v
                                        #if k=='reply' and isinstance(v, DWIO):
                                        #    reply = v
                                        #elif k=='reply' and isinstance(v, str):
                                        #    msg = v
                                        else:
                                            if isinstance(v, str):
                                                    v = "'%s'" % v
                                            e = '%s=%s' % (k,v)
                                            if self.debug:
                                                    print(e)
                                            exec(e)
                                #if isinstance(reply, DWIO):
                                #res = reply
			if isinstance(res, str) or msg:
                                if msg:
                                    reply = msg
                                #print res
				elif res.startswith("FAIL") or res.startswith("ERROR") or res.startswith("OK"):
					reply = res
				else:
					reply += res
				if self.cmdAutoClose and not self.online:
					self.connected = False
			#elif isinstance(res, dict):
			#	for k,v in res.items():
			#		if isinstance(v, str):
			#			v = "'%s'" % v
			#		e = '%s=%s' % (k,v)
			#		if self.debug:
			#			print(e)
                        #                print(e)
                        #                if k=='reply' and isinstance(v, DWIO):
                        #                    reply = v
                        #                else:
                        #                    exec(e)
                        #        if isinstance(reply, DWIO):
                        #            res = reply
			if isinstance(res, DWSocketListener) or isinstance(obj, DWSocketListener):
                                if obj:
                                    res = obj
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
			elif isinstance(res, DWIO) or isinstance(obj, DWIO):
                                if obj:
                                    res = obj
				self.online = True
				self.conn = res
				b = self.conn.binding
				if b:
					reply = "OK attaching to connection %s\r" % (b)
				else:
                                        if not msg:
                                            r = "OK connected to %s:%s" % (self.conn.host, self.conn.port)
                                            reply = r + "\n" + r + "\r\n"
                                        else:
                                            reply = msg + "\r\n"

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

	def write(self, data, ifs=('\r','\n')):
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
			for c in ifs:
				pos = self.wbuf.find(c)
				if pos >= 0:
					break
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
					wdata = wdata.lstrip().rstrip()
					if wdata:
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
                        if self.cmdAutoClose:
                            self.rb.close()
		#if not self.conn:
		d=self._outWaiting()
		if self.debug:
			print "ch:%d ow:i=%d" % (ord(self.channel), d)
		#if d>=0 and self.conn:
		if d==0 and self.conn:
		#else:
			d = self.conn.outWaiting()
                        if not self.cmdAutoClose and not self.conn.isConnected() and self.online:
                            reply = "\r\nNO CARRIER\r\n"
                            self.rb.add(len(reply))
                            self.rq.put(reply)
                            self.online = False
			if self.debug:
				print "ch:%d ow:c=%d" % (ord(self.channel), d)
			if d <= 0 and not self.conn.isConnected():
				self.conn = None
				self.online = False
                                if self.cmdAutoClose:
                                    self.rb.close()
                                    self.connected = False
                                else:
                                    d = 0
                if d <= 0 and not self.cmdAutoClose:
                    d = 0
		return d

	def _close(self):
                print("%s: closing" % self)
		if self.conn:
			self.conn.close()
                #if not self.cmdAutoClose and self.online:
                #    reply = "\r\nNO CARRIER\r\n"
                #    self.rb.add(len(reply))
                #    self.rq.put(reply)
		for c in self.listeners:
			c.close()
		self.conn = None
		self.online = False
                if self.cmdAutoClose:
                    self.rb.close()
                    self.connected = False

        def isConnected(self):
            state = self.connected
            if self.conn:
                state = self.conn.isConnected()
            if not self.cmdAutoClose:
                # hack
                state = True
            return state
                
