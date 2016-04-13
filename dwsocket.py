#!/usr/local/bin/python
import socket
import threading
from dwio import DWIO
import time

class DWSocket(DWIO):
	def __init__(self, host='localhost', port=6809):
		DWIO.__init__(self, blocking=True)
		self.host = host
		self.port = int(port)
		self.sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM)
		self.sock.bind(('0.0.0.0', self.port))
		self.conn = None
		self.addr = None

	def connect(self):
		self.sock.connect((self.host, self.port))

	def accept(self):
		self.sock.listen(0)
		(self.conn, self.addr) = self.sock.accept()
		print( "Accepted Connection: %s" % str(self.addr))
		return

	def _read(self, count=256):
		data = ''
		if not self.conn:
			self.accept()
		try:
			#print "waiting..."
			data = self.conn.recv(count)
		except Exception as e:
			print str(e)
			time.sleep(0.1)
		if not data:
			print "Connection closed"
			self.conn=None
		#if data:
		#	print "r",data
		return data

	def _write(self, data):
		n = 0
		try:
			if self.conn:
				#print "w",data
				n = self.conn.send(data)
		except Exception as e:
			print str(e)

		return n

	def _in_waiting(self):
		return False
		#return self.sock.in_waiting
		
	def close(self):
		self.sock.close()

if __name__ == '__main__':
	import sys


	sock = DWSocket()
	
	def cleanup():
		#print "main: Closing sockial port."
		sock.close()
	import atexit
	atexit.register(cleanup)

	try:
		sock.accept()
		while True:
			print ">",
			wdata = raw_input()
			sock.write(wdata)
			sock.write("\n> ")
			#print "main: Wrote %d bytes" % len(wdata)
			rdata = sock.readline()
			#print "main: Read %d bytes" % len(rdata)
			print rdata,
	finally:
		cleanup()
