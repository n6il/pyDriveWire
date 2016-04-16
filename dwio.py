#!/usr/local/bin/python
import threading
import Queue
#from collections import deque
from time import sleep

class DWIO:
	def __init__(self, rwf=None, inf=None, outf=None, blocking=False):
		self.abort = False

		if rwf:
			inf = outf = rwf
		self.inf = inf
		self.outf = outf
		self.rt = threading.Thread(target=self._readHandler, args=())
		self.rt.daemon = True
		self.rq = Queue.Queue()
		self.rbuf = ''
		self.wt = threading.Thread(target=self._writeHandler, args=())
		self.wt.daemon = True
		self.wq = Queue.Queue()
	

	def readline(self, ifs='\n'):
		return self.read(readLine=True, ifs=ifs)

	def read(self, rlen=None, readLine=False, ifs='\n'):
		rdata=''
		pos=-1
		#print "dwio read %d" % rlen
		if not self.rt.is_alive():
			# Start the background reader thread only
			# when someone asks to start reading from it
			self.rt.start()
		while not self.abort:
			d = ''
			if self.rbuf:
				d = self.rbuf
				self.rbuf = ''
			else:
				try:
					d = self.rq.get(True, 1)
				except Exception as e:
					pass
					#print str(e)
			available = len(d)
			required = available
			#print rlen, len(rdata), available, len(self.rbuf)
			if not available:
				#print "waiting2"
				continue
			if rlen:
				required = min (rlen-len(rdata), available)
			if readLine:
				pos = d.find(ifs)
				if pos >= 0:
					required = pos+1
			rdata += d[:required]

			if (required < available):
				self.rbuf = d[required:]
			if readLine:
				if pos >= 0:
					break
				else:
					continue
			if not rlen and self.rq.empty():
				break
			if len(rdata) == rlen:
				break

		#print "reading: %d (%s)" %(len(rdata),rdata if ord(rdata)>32 and ord(rdata)<128 else '.')
		return rdata

	def write(self, data):
		if not self.wt.is_alive():
			# Start the background reader thread only
			# when someone asks to start reading from it
			self.wt.start()
		self.wq.put(data)
		return len(data)

	def _close(self):
		pass

	def close(self):
		self.abort = True
		self._close()
		print "Shutting down async io threads..."
		if self.rt.is_alive():
			self.rt.join()
		if self.wt.is_alive():
			self.wt.join()

	def _readHandler(self):
		while not self.abort:
			d=self._read()
			if d:
				#print "put: (%s)" % d
				self.rq.put(d)

	def _read(self, rlen=None):
		data = ''
		ri = []
		try:
			(ri, _, _) = select.select([inf.fileno()], [], [], 1)
		except:
			pass
		if any(ri):
			data = self.inf.read(rlen)
		return data

	def _writeHandler(self):
		while not self.abort:
			d = ''
			try:
				d = self.wq.get(True, 1)
			except Exception as e:	
				pass
				#print str(e)	

			if d:
				#"wh: %d" % len(d)
				self._write(d)

	def _write(self, data):
		return self.outf.write(data)



	
class DWIO2:
	def __init__(self, rwf=None, inf=None, outf=None, blocking=False):
		self.Abort = False

		self.rqueue = deque()
		if rwf:
			inf = outf = rwf
		self.inf = inf
		self.outf = outf
		self.blocking = blocking
		if not self.blocking:
			self.rt = threading.Thread(target=self._readHandler, args=())
			self.rt.daemon = True

	def write(self, data):
		#print "write %d" % len(data)
		return self._write(data)

	def readline(self, ifs='\n'):
		return self.read(readLine=True, ifs=ifs)

	def read(self, rlen=None, readLine=False, ifs='\n'):
		rdata=''
		pos=-1
		#print "dwio read %d" % rlen
		if not self.blocking and not self.rt.is_alive():
			# Start the background reader thread only
			# when someone asks to start reading from it
			self.rt.start()
		while True:
			if self.blocking:
				self.rqueue.appendleft(self._read(rlen))
			if len(self.rqueue):
				d = self.rqueue.pop()
				available = len(d)
				required = available
				if rlen:
					required = min (rlen-len(rdata), available)
				if readLine:
					pos = d.find(ifs)
					if pos >= 0:
						required = pos+1
				rdata += d[:required]

				if (required < available):
					self.rqueue.append(d[required:])
			if readLine:
				if pos >= 0:
					break
				else:
					continue
			if not rlen and not len(self.rqueue):
				break
			if len(rdata) == rlen:
				break

		return rdata

	def close(self):
		self.Abort = True
		self.rt.join()

	def _readHandler(self):
		while True and not self.Abort:
			d=self._read()
			if d:
				self.rqueue.appendleft(d)

	def _read(self, rlen=None):
		return self.inf.read(rlen)

	def _write(self, data):
		return self.outf.write(data)


class DWIOStdIo(DWIO):
	def __init__(self):
		DWIO.__init__(self, blocking=True)

	def _read(self, count=None):
		return raw_input()+'\n'

	def _write(self, data):
		sys.stdout.write(data)

if __name__ == '__main__':
	import sys
	#f=open("fifo")
	#dw=DWIO(f)
	dw = DWIOStdIo()
	while True:
		dw.write("> ");
		dw.write(dw.readline())

