#!/usr/local/bin/python
import socket
import threading
from dwio import DWIO
import time
import select

class DWSocket(DWIO):
	def __init__(self, host='localhost', port=6809):
		DWIO.__init__(self, blocking=True)
		self.host = host
		self.port = int(port)
		self.sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM)
		self.conn = None
		self.addr = None

	def connect(self):
		self.sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM)
		self.sock.connect((self.host, self.port))
		self.conn = self.sock

	def _read(self, count=256):
		data = None
		if self.abort or not self.conn:
			return ''
		ri = []
		try:
			(ri, _, _) = select.select([self.conn.fileno()], [], [], 1)
		except Exception as e:
			print str(e)
			print "Connection closed"
			self._close()
		if any(ri):
			#print "reading"
			data = self.conn.recv(count)
		#else:
			#print "waiting"
		if data == '':
			print "Connection closed"
			self._close()
		#if data:
		#	print "r",data
		return data

	def _write(self, data):
		if self.abort or not self.conn:
			return -1
		n = 0
		wi = []
		try:
			(_, wi, _) = select.select([], [self.conn.fileno()], [], 1)
		except Exception as e:
			print str(e)
			print "Connection closed"
			self._close()
			n = -1
		if any(wi):
			try:
				n = self.conn.send(data)
			except Exception as e:
				print str(e)
				self._close()
				n = -1

		return n

	def _in_waiting(self):
		if self.abort or not self.conn:
			return False
		ri = []
		try:
			(ri, _, _) = select.select([self.conn.fileno()], [], [], 1)
		except Exception as e:
			print str(e)
			print "Connection closed"
			self._close()
		return any(ri)
		#return self.sock.in_waiting
		
	def _close(self):
		#if not self.conn:
		#	return
		ri = wi = []
		try:
			(ri, wi, _) = select.select([self.conn.fileno()], [self.conn.fileno()], [], 0)
		except Exception as e:
			pass
			#print str(e)
			#print "Connection closed"
		if any(ri+wi):
			print "Closing: connection"
			try:
				#self.conn.shutdown(socket.SHUT_RDWR)
				self.conn.close()
			except:
				pass
		#if any(wi):
		#	print "Closing socket"
		#	try:
		#		self.conn.shutdown(socket.SHUT_RDWR)
		#	except:
		#		pass
		self.conn = None
		#self.sock.shutdown(socket.SHUT_RDWR)

	def _cleanup(self):
		self.abort = True
		self._close()
		if self.sock:
			print "Closing: socket"
			try:
				self.sock.close()
			except:
				pass
			self.sock = None

class DWSocketServer(DWSocket):
	def __init__(self, host='localhost', port=6809):
		DWSocket.__init__(self, host=host, port=port)
		self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.sock.bind(('0.0.0.0', self.port))

	def accept(self):
		while not self.abort:
			self.conn = None
			try:
				r = self.sock.listen(0)
				(self.conn, self.addr) = self.sock.accept()
				print( "Accepted Connection: %s" % str(self.addr))
			except Exception as ex:
				print("Server Aborted", str(ex))
			
			if self.conn:
				break
			print "looping"

	def _read(self, count=256):
		data = None
		if not self.conn:
			self.accept()
		return DWSocket._read(self, count)


if __name__ == '__main__':
	import sys


	sock = DWSocketServer()
	
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
