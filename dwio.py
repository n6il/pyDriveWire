#!/usr/local/bin/python
import threading
import Queue
from time import sleep

class DWIO:
	def __init__(self):
		self.Abort = False

		self.wqueue = Queue.Queue()
		self.wt = threading.Thread(target=self._writeHandler, args=())
		self.wt.daemon = True
		self.wt.start()

	def write(self, data):
		#print "write %d" % len(data)
		self.wqueue.put(data)
		#self._writer(data)

	def _writeHandler(self):
		while True and not self.Abort:
			#if not self.wqueue.empty():
			data=self.wqueue.get(True, None)
			#print "_writeHandler: Got %d" % len(data)
			self._writer(data)

	def _writer(self, data, i=0):
		#print  "writer: writing ..."
		wlen=len(data)
		written = 0
		bs=16
		while (written < wlen):
			#ow = self.ser.outWaiting()
			#while ow>0:
			#	print "ow: %d" % ow
			e=min(written+bs,wlen)
			d=data[written:e]
			wrote = self._write(d)
			#print  "writer: wrote %s" % wrote
			written += wrote
			#while self.ser.outWaiting()>0:
				#print self.ser.outWaiting()
			self.ser.flush()
			#sleep(0.01)
		#print  "writer: written %s" % written

	def read(self, rlen=None, blocking=True):
		rdata=''
		
		if rlen and rlen>0:
			while len(rdata) < rlen and not self.Abort:
				d = self._read(rlen-len(rdata))
				#print "reader: read: %d" % len(d)
				if not blocking and len(d) == 0:
				  break
				if d:
					rdata += d
		elif rlen==None:
			while self._in_waiting():
				d = self._read(1)
				if len(d) == 0:
					break
				rdata += d
			
		return rdata

	def close(self):
		self.Abort = True
		self.wt.join()
		self.ser.close()

