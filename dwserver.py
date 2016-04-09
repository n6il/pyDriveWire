import time
from struct import *
from ctypes import *
import traceback

from dwconstants import *
from dwchannel import DWSerialChannel


Nulldata = NULL * SECSIZ

def dwCrc16(data):
	checksum = 0
	#for c in data:
	#	checksum = c_ushort(checksum + ord(c)).value	
	checksum = sum(bytearray(data))
	return pack(">H", checksum)

class DWServer:
	def __init__(self, conn):
		self.conn = conn
		self.files = [None, None, None, None]
		self.channels = {}

	def open(self, disk, fileName):
		self.files[disk] = open(fileName,"r+")
		print('Opened: %s' % fileName)
		self.files[disk].seek(0)

	def close(self, disk):
		d = self.files[disk]
		if d:
			print('Closing: %s' % d.name)
			d.close()
			self.files[disk] = None

	def cmdStat(self, cmd):
		info = self.conn.read(STATSIZ)
		(disk, stat) = unpack(">BB", info)
		print "cmd=%0x cmdStat disk=%d stat=%s" % (ord(cmd), disk, hex(stat))
		
	def cmdRead(self, cmd, flags=''):
		rc = E_OK
		info = self.conn.read(INFOSIZ)
		(disk, lsn) = unpack(">BI", info[0]+NULL+info[1:])
		#print "cmd=%0x cmdRead disk=%d lsn=%d" % (ord(cmd), disk, lsn)
		data = Nulldata
		if self.files[disk] == None:
			rc = E_NOTRDY
		if rc == E_OK:
			try:
				self.files[disk].seek(lsn*SECSIZ)
				assert(self.files[disk].tell() == (lsn*SECSIZ))
			except:
				rc = E_SEEK
				data = Nulldata
				print "   rc=%d" % rc
		if rc == E_OK:
			try:
				data = self.files[disk].read(SECSIZ)
				if len(data)==0:
					data = Nulldata
					flags += 'E'
			except:
				rc = E_READ
		self.conn.write(chr(rc))
		self.conn.write(dwCrc16(data))
		self.conn.write(data)
		#print "   rc=%d" % rc

	def cmdReRead(self, cmd):
		self.cmdRead(cmd, 'R')

	def cmdReadEx(self, cmd, flags=''):
		rc = E_OK
		flags=''
		info = self.conn.read(INFOSIZ)
		(disk, lsn) = unpack(">BI", info[0]+NULL+info[1:])
		data = Nulldata
		if self.files[disk] == None:
			rc = E_NOTRDY
			#print "   rc=%d" % rc
		if rc == E_OK:
			try:
				self.files[disk].seek(lsn*SECSIZ)
				#assert(self.files[disk].tell() == (lsn*SECSIZ))
			except:
				rc = E_SEEK
				#print "   rc=%d" % rc
				traceback.print_exc()
		if rc == E_OK:
			try:
				data = self.files[disk].read(SECSIZ)
				#if data:
				#	pass
				#print "cmdReadEx read %d" % len(data)
				if len(data)==0:
					# Seek past EOF, just return 0'ed data
					data = Nulldata
					flags += 'E'
					#print "cmdReadEx eof read %d" % len(data)
				
			except:
				rc = E_READ
				data = Nulldata
				#print "   rc=%d" % rc
				traceback.print_exc()
		#print "cmdReadEx sending %d" % len(data)
		self.conn.write(data)

		crc = self.conn.read(CRCSIZ)
		#print "   len(info)=%d" % len(info)
		#(crc,) = unpack(">H", info)
		
		if rc == E_OK:
			if crc != dwCrc16(data):
				rc = E_CRC
		self.conn.write(chr(rc))
		#print "cmd=%0x cmdReadEx disk=%d lsn=%d rc=%d f=%s" % (ord(cmd), disk, lsn, rc, flags)
		#print "   rc=%d" % rc

	def cmdReReadEx(self, cmd):
		self.cmdReadEx(cmd, 'R')

	def cmdWrite(self, cmd):
		#print "cmd=%0x cmdWrite" % ord(cmd)
		rc = E_OK
		info = self.conn.read(INFOSIZ)
		data = self.conn.read(SECSIZ)
		crc = self.conn.read(CRCSIZ)
		(disk, lsn) = unpack(">BI", info[0]+NULL+info[1:])
		if crc != dwCrc16(data):
			rc=E_CRC
		if rc == E_OK and self.files[disk] == None:
			rc = E_NOTRDY
		if rc == E_OK:
			try:
				self.files[disk].seek(lsn*SECSIZ)
			except:
				traceback.print_exc()
				rc = E_SEEK
		if rc == E_OK:
			try:
				self.files[disk].write(data)
				self.files[disk].flush()
			except:
				rc = E_WRITE
				print traceback.print_exc()
		#if crc != dwCrc16(data):
		#	rc=E_CRC
		self.conn.write(chr(rc))
		print "cmd=%0x cmdWrite disk=%d lsn=%d rc=%d" % (ord(cmd), disk, lsn, rc)
		#print "   rc=%d" % rc

	# XXX Java version will return oldest data first
	def cmdSerRead(self, cmd):
		data = NULL * 2
		#msg = "NoData"
		msg = ""
		for channel in self.channels:
			nchannel = ord(channel)
			ow = self.channels[channel].outWaiting()
			if ow<0:
				# Channel is closing
				data = chr(16)
				data += channel
				msg = "channel=%d Closing" % nchannel
				break
			elif ow==0:
				continue
			elif ow<3:
				data = channel
				data += self.channels[channel].read(1)
				msg = "channel=%d ByteWaiting=(%s)" % (nchannel, data[1])
				break
			else:
				data = chr(17+nchannel)
				data += chr(ow)
				msg = "channel=%d BytesWaiting=%d" % (nchannel, ow)
				break
		#elif ow<0:
		#	# Channel is closing
		#	data = chr(16)
		#	data += chr(1)
	
		self.conn.write(data)
		if msg:
			print "cmd=%0x serRead %s" % ( ord(cmd), msg )

	# XXX
	def cmdReset(self, cmd):
		print "cmd=%0x cmdReset" % ord(cmd)

	# XXX
	def cmdInit(self, cmd):
		print "cmd=%0x cmdInit" % ord(cmd)

	def cmdNop(self, cmd):
		print "cmd=%0x cmdNop" % ord(cmd)

	# XXX
	def cmdTerm(self, cmd):
		print "cmd=%0x cmdTerm" % ord(cmd)

	def cmdDWInit(self, cmd):
		print "cmd=%0x cmdDWInit" % ord(cmd)
		self.conn.write(chr(0xff))

	def cmdTime(self, cmd):
		t=''
		now=time.localtime()
		t += chr(now.tm_year - 1900)
		t += chr(now.tm_mon)
		t += chr(now.tm_mday)
		t += chr(now.tm_hour)
		t += chr(now.tm_min)
		t += chr(now.tm_sec)
		print "cmd=%0x cmdTime %s" % (ord(cmd), time.ctime())
		self.conn.write(t)
		
	def cmdSerSetStat(self, cmd):
		channel = self.conn.read(1)
		code = self.conn.read(1)
		if code == SS_ComSt:
			data = self.conn.read(26)
		else:
			data = ''
		print("cmd=%0x cmdSerSetStat channel=%d code=%0x len=%d" % (ord(cmd),ord(channel), ord(code), len(data)))

	def cmdSerGetStat(self, cmd):
		channel = self.conn.read(1)
		code = self.conn.read(1)
		print("cmd=%0x cmdSerGetStat channel=%d code=%0x" % (ord(cmd),ord(channel), ord(code)))

	def cmdSerInit(self, cmd):
		channel = self.conn.read(1)
		self.channels[channel] = DWSerialChannel(self, channel)
		print("cmd=%0x cmdSerInit channel=%d" % (ord(cmd),ord(channel)))

	def cmdSerTerm(self, cmd):
		channel = self.conn.read(1)
		del self.channels[channel]
		print("cmd=%0x cmdSerTerm channel=%d" % (ord(cmd),ord(channel)))

	def cmdFastWrite(self, cmd):
		channel = ord(cmd)-0x80
		byte = self.conn.read(1)
		self.channels[chr(channel)].write(byte)
		print("cmd=%0x cmdFastWrite channel=%d byte=%0x (%c)" % (ord(cmd),channel,ord(byte), byte if byte>=' ' and byte <='~' else '.'))

	def cmdSerReadM(self, cmd):
		channel = self.conn.read(1)
		num = self.conn.read(1)
		data = self.channels[channel].read(ord(num))
		self.conn.write(data)	
		print("cmd=%0x cmdSerReadM channel=%d num=%d" % (ord(cmd),ord(channel), ord(num)))

	def cmdSerWrite(self, cmd):
		channel = self.conn.read(1)
		byte = self.conn.read(1)
		self.channels[channel].write(byte)
		print("cmd=%0x cmdSerWrite channel=%d byte=%0x" % (ord(cmd),channel,ord(byte)))


	def cmdErr(self, cmd):
		print("cmd=%0x cmdErr" % ord(cmd))
		#raise Exception("cmd=%0x cmdErr" % ord(cmd))

	# Command jump table
	dwcommand = {
		OP_NOP: cmdNop,
		OP_TIME: cmdTime,
		OP_GETSTAT: cmdStat,
		OP_INIT: cmdInit,
		OP_READ: cmdRead,
		OP_SERREAD: cmdSerRead,
		OP_SETSTAT: cmdStat,
		OP_TERM: cmdTerm,
		OP_WRITE: cmdWrite,
		OP_DWINIT: cmdDWInit,
		OP_REREAD: cmdReRead,
		OP_READEX: cmdReadEx,
		OP_REREADEX: cmdReReadEx,
		OP_RESET3: cmdReset,
		OP_RESET2: cmdReset,
		OP_RESET1: cmdReset,
		OP_SERSETSTAT: cmdSerSetStat,
		OP_SERGETSTAT: cmdSerGetStat,
		OP_SERINIT: cmdSerInit,
		OP_SERTERM: cmdSerTerm,
		OP_FASTWRITE1: cmdFastWrite,
		OP_SERREADM: cmdSerReadM,
		OP_SERWRITE: cmdSerWrite,
	}

	def main(self):
		while True:
			cmd = self.conn.read(1)
			if cmd:
				try:
					f=DWServer.dwcommand[cmd]
				except KeyError:
					f = lambda s,x: DWServer.cmdErr(s,x)
				f(self,cmd)

class TestConn:
	def __init__(self):
		self.i=0
	def read(self, n):
		cmd=DWServer.dwcommand.keys()[self.i]
		self.i = (self.i+1) % len(DWServer.dwcommand.keys())
		return cmd
	def write(self, buf):
		for c in buf:
			d = c if (ord(c)>=32 and ord(c)<128) else '.'
			print "%s(%s) " % (hex(ord(c)), d),
		print

if __name__ == '__main__':
	testConn = TestConn()
	server = DWServer(testConn)
	server.main()

