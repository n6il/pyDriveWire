#!/usr/local/bin/python
import socket
import threading
from dwio import DWIO

class DWSocket(DWIO):
	def __init__(self, host='localhost', port=6809):
		DWIO.__init__(self)
		self.host = host
		self.port = int(port)
		self.sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM)
		self.conn = None
		self.addr = None

	def connect(self):
		self.sock.connect((self.host, self.port))

	def accept(self):
		self.sock.bind('0,0,0,0', self.port)
		self.sock.listen(0)
		(self.conn, self.addr) = self.sock.accept()
		print( "Accepted Connection: %s" % str(self.addr))
		return

	def _read(self, count):
		return self.conn.recv(count)

	def _write(self, data):
		return self.sock.send(data)

	def _in_waiting(self):
		return False
		#return self.sock.in_waiting
		
if __name__ == '__main__':
	import sys

	if len(sys.argv) < 2:
		print("Usage: %s <port> <speed>" % (sys.argv[0]))
		print('')
		print('\t%s /dev/tty.usbsockial-FTF4ZN9S 19200' % sys.argv[0])
		print('')
		sys.exit(1)

	(_, port, speed) = sys.argv
	sock = DWSerial(port, speed)
	
	def cleanup():
		#print "main: Closing sockial port."
		sock.close()
	import atexit
	atexit.register(cleanup)

	try:
		while True:
			wdata = raw_input()
			sock.write(wdata)
			#print "main: Wrote %d bytes" % len(wdata)
			rdata = sock.read(len(wdata))
			#print "main: Read %d bytes" % len(rdata)
			print rdata
	finally:
		cleanup()
