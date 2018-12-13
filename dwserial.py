#!/usr/local/bin/python
import serial
from dwio import DWIO
import dwlib

class DWSerial(DWIO):
	def __init__(self, port, speed, rtscts=False):
		DWIO.__init__(self, threaded=True)
		self.port = port
		self.speed = speed
		self.rtscts = rtscts
		self.ser = None

        def name(self):
            return "%s %s %s" % (self.__class__, self.port, self.speed)

	def isConnected(self):
		return self.ser != None

	def connect(self):
		self.ser = serial.Serial(self.port, self.speed, timeout=1, rtscts=self.rtscts)
		self.connected = True
		return

	def _close(self):
		self.ser = None
		self.connected = False
		pass
		#self.ser.close()

	def _read(self, count=None):
		if self.abort:
			return ''
		data = ''
		#print "dwserial: read"
		if count:
			data = self.ser.read(count)
		else:
			data = self.ser.read()

		if self.debug and data:
			print "serread: len=%d %s"%(len(data),dwlib.canonicalize(data))
		return data

	def _write(self, data):
		if self.abort:
			return -1
		if self.debug and data:
			print "serwrite: len=%d %s"%(len(data),dwlib.canonicalize(data))
		return self.ser.write(data)

	def _in_waiting(self):
		return self.ser.in_waiting
		
if __name__ == '__main__':
	import sys

	if len(sys.argv) < 2:
		print("Usage: %s <port> <speed>" % (sys.argv[0]))
		print('')
		print('\t%s /dev/tty.usbserial-FTF4ZN9S 19200' % sys.argv[0])
		print('')
		sys.exit(1)

	(_, port, speed) = sys.argv
	ser = DWSerial(port, speed)
	ser.connect()
	
	def cleanup():
		#print "main: Closing serial port."
		ser.close()
	import atexit
	atexit.register(cleanup)

	try:
		while True:
			wdata = raw_input()
			ser.write(wdata)
			print "main: Wrote %d bytes" % len(wdata)
			rdata = ser.read(len(wdata))
			print "main: Read %d bytes" % len(rdata)
			print rdata
	finally:
		cleanup()
