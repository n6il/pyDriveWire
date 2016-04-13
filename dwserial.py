#!/usr/local/bin/python
import serial
from dwio import DWIO

class DWSerial(DWIO):
	def __init__(self, port, speed):
		DWIO.__init__(self, blocking=True)
		self.port = port
		self.speed = speed
		self.ser = None

	def connect(self):
		self.ser = serial.Serial(self.port, self.speed, timeout=None)
		return

	def _read(self, count=None):
		if count:
			return self.ser.read(count)
		else:
			return self.ser.read()

	def _write(self, data):
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
