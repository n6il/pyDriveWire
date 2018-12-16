import time
from struct import *
from ctypes import *
import traceback
import os

from dwconstants import *
from dwchannel import DWVModem
from dwfile import DWFile
from dwutil import *

from cococas import *

NULL_SECTOR = NULL * SECSIZ

class DWServer:
	def __init__(self, args, conn, version, instances, instance):
		self.conn = conn
		self.files = [None] * 256
		self.channels = {}
		self.connections = {}
		self.debug = False
		self.timeout = 5.0
		self.version = version
		self.vprinter = None

                self.emCeeDir = []
                self.emCeeDirIdx = 0
		if args.experimental:
			if 'printer' in args.experimental:
                                print("DWServer: Enabling experimental printing support")
                                from dwprinter import DWPrinter
				self.vprinter = DWPrinter()
                self.emCeeAliases = {}
                self.instances = instances
                self.instance = instance

	def registerConn(self, conn):
		n = None
		i = 0
		si = "1"
		while i<=len(self.connections):	
			n = self.connections.get(si, None)
			if not n:
				break
			i += 1
			si = "%d" % (i+1)
		self.connections[si] = conn
		return si

				
	def open(self, disk, fileName):
		self.files[disk] = DWFile(fileName,"rb+")
		print('Opened: disk=%d file=%s' % (disk, fileName))
		self.files[disk].file.seek(0)

	def close(self, disk):
		d = self.files[disk]
		if d and isinstance(d, DWFile):
			name = d.file.name
			print('Closing: disk=%d file=%s' % (disk, d.name))
			d.file.close()
			if d.remote:
				d._delete()
                if d:
                    self.files[disk] = None

	def closeAll(self):
                for disk in range(len(self.files)):
                    if self.files[disk]:
                        self.close(disk)

	def cmdStat(self, cmd):
		info = self.conn.read(STATSIZ, self.timeout)
		if not info:
			print "cmd=%0x cmdStat timeout getting info" % (ord(cmd))
			return
		(disk, stat) = unpack(">BB", info)
		if self.debug:
			print "cmd=%0x cmdStat disk=%d stat=%s" % (ord(cmd), disk, hex(stat))
		
	def cmdRead(self, cmd, flags=''):
		disk = -1
		lsn = -1
		rc = E_OK
		info = self.conn.read(INFOSIZ, self.timeout)
		if not info:
			print "cmd=%0x cmdRead timeout getting info" % (ord(cmd))
			return
			# rc = E_READ
			#rc = E_CRC # force a re-read
		#if rc == E_OK:
		(disk, lsn) = unpack(">BI", info[0]+NULL+info[1:])
		if self.debug:
			print "cmd=%0x cmdRead disk=%d lsn=%d" % (ord(cmd), disk, lsn)
		data = NULL_SECTOR
		if rc == E_OK:
			if self.files[disk] == None:
				rc = E_NOTRDY
                # XXX: Not needed if set on open and updated on write
                #if rc == E_OK and lsn == 0:
                #        self.files[disk].guessMaxLsn()
                if rc == E_OK and lsn >= self.files[disk].maxLsn:
                        rc = E_EOF
		if rc == E_OK:
			try:
				self.files[disk].file.seek(lsn*SECSIZ)
				assert(self.files[disk].file.tell() == (lsn*SECSIZ))
			except:
				rc = E_SEEK
				data = NULL_SECTOR
				print "   rc=%d" % rc
		if rc == E_OK:
			try:
				data = self.files[disk].file.read(SECSIZ)
				if len(data)==0:
					data = NULL_SECTOR
					flags += 'E'
			except:
				rc = E_READ
		self.conn.write(chr(rc))
		self.conn.write(dwCrc16(data))
		self.conn.write(data)
		if self.debug:
			print "   rc=%d" % rc

	def cmdReRead(self, cmd):
		self.cmdRead(cmd, 'R')

	def cmdReadEx(self, cmd, flags=''):
		disk = -1
		lsn = -1
		rc = E_OK
		flags=''
		info = self.conn.read(INFOSIZ, self.timeout)
		if not info:
			print "cmd=%0x cmdReadEx timeout getting info" % (ord(cmd))
			return
			#rc = E_READ
			#rc = E_CRC # force a re-read
		if rc == E_OK:
			(disk, lsn) = unpack(">BI", info[0]+NULL+info[1:])
		data = NULL_SECTOR
		if self.files[disk] == None:
			rc = E_NOTRDY
			#print "   rc=%d" % rc
                # XXX: not needed if it's set on open and updated on write
                #if rc == E_OK and lsn == 0:
                #        self.files[disk].guessMaxLsn()
                if rc == E_OK and lsn >= self.files[disk].maxLsn:
                        rc = E_EOF
		if rc == E_OK:
			try:
				self.files[disk].file.seek(lsn*SECSIZ)
				assert(self.files[disk].file.tell() == (lsn*SECSIZ))
			except:
				rc = E_SEEK
				#print "   rc=%d" % rc
				traceback.print_exc()
		if rc == E_OK:
			try:
				data = self.files[disk].file.read(SECSIZ)
				#if data:
				#	pass
				#print "cmdReadEx read %d" % len(data)
				if len(data)==0:
					# Seek past EOF, just return 0'ed data
					data = NULL_SECTOR
					flags += 'E'
					#print "cmdReadEx eof read %d" % len(data)
				
			except:
				rc = E_READ
				data = NULL_SECTOR
				#print "   rc=%d" % rc
				traceback.print_exc()
		#print "cmdReadEx sending %d" % len(data)
		dataCrc = dwCrc16(data)
		self.conn.write(data)

		crc = self.conn.read(CRCSIZ, 1)
		if not crc:
			print "cmd=%0x cmdReadEx timeout getting crc" % (ord(cmd))
			#return
			rc = E_CRC
		#print "   len(info)=%d" % len(info)
		#(crc,) = unpack(">H", info)
		
		if rc == E_OK:
			if crc != dataCrc:
				print "CRC: read",hex(unpack(">H",crc)[0]), "expected",hex(unpack(">H",dataCrc)[0])
				rc = E_CRC
		self.conn.write(chr(rc))
		if self.debug or rc != E_OK:
			print "cmd=%0x cmdReadEx disk=%d lsn=%d rc=%d f=%s" % (ord(cmd), disk, lsn, rc, flags)
		#print "   rc=%d" % rc

	def cmdReReadEx(self, cmd):
		self.cmdReadEx(cmd, 'R')

	def cmdWrite(self, cmd, flags=''):
		#print "cmd=%0x cmdWrite" % ord(cmd)
		rc = E_OK
		disk = -1
		lsn = -1
		data = ''
		info = self.conn.read(INFOSIZ, self.timeout)
		if not info:
			print "cmd=%0x cmdWrite timeout getting info" % (ord(cmd))
			return
			#rc = E_WRITE
			#rc = E_CRC # force a re-write
		if rc == E_OK:
			data = self.conn.read(SECSIZ, self.timeout)
		if not data:
			print "cmd=%0x cmdWrite timeout getting data" % (ord(cmd))
			#return
			#rc = E_WRITE
			rc = E_CRC # force a re-write
		if rc == E_OK:
			crc = self.conn.read(CRCSIZ, self.timeout)
			if not crc:
				print "cmd=%0x cmdWrite timeout getting crc" % (ord(cmd))
				#return
				rc = E_CRC # force a re-write
			else:
				(disk, lsn) = unpack(">BI", info[0]+NULL+info[1:])
				if crc != dwCrc16(data):
					rc=E_CRC
		if rc == E_OK and self.files[disk] == None:
			rc = E_NOTRDY
		if rc == E_OK:
                    # Note: Write is allowed for non-os9 images
                    if self.files[disk].os9Image and lsn >= self.files[disk].maxLsn:
                        rc = E_EOF
		if rc == E_OK:
			try:
				self.files[disk].file.seek(lsn*SECSIZ)
			except:
				traceback.print_exc()
				rc = E_SEEK

		if rc == E_OK:
			try:
				self.files[disk].file.write(data)
				self.files[disk].file.flush()
			except:
				rc = E_WRITE
				print traceback.print_exc()
                if rc == E_OK:
                    if (lsn == 0) or (not self.files[disk].os9Image and lsn >= self.files[disk].maxLsn):
                       self.files[disk].guessMaxLsn() 
		#if crc != dwCrc16(data):
		#	rc=E_CRC
		self.conn.write(chr(rc))
		if self.debug or rc != E_OK:
			print "cmd=%0x cmdWrite disk=%d lsn=%d rc=%d f=%s" % (ord(cmd), disk, lsn, rc, flags)
		#print "   rc=%d" % rc

	def cmdReWrite(self, cmd):
		self.cmdWrite(cmd, 'R')

	# XXX Java version will return oldest data first
	def cmdSerRead(self, cmd):
		data = NULL * 2
		msg = "NoData"
		#msg = ""
		for channel in self.channels:
			nchannel = ord(channel)
			ow = self.channels[channel].outWaiting()
			if ow<0:
				# Channel is closing
				data = chr(16)
				data += channel
				msg = "channel=%d Closing" % nchannel
				self.channels[channel].close()
                                del self.channels[channel]
				break
			elif ow==0:
				continue
			elif ow<3:
				data = chr(1+nchannel)
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
		if self.debug and msg:
			print "cmd=%0x serRead %s" % ( ord(cmd), msg )

	# XXX
	def cmdReset(self, cmd):
		if self.debug:
			print "cmd=%0x cmdReset" % ord(cmd)

	# XXX
	def cmdInit(self, cmd):
		for drive in range(len(self.files)):
			if not self.files[drive]:
				continue
			path = self.files[drive].file.name
			self.close(drive)
			self.open(drive, path)
			print "cmdInit: reset(%d, %s)" % (int(drive), path)
		if self.debug:
			print "cmd=%0x cmdInit" % ord(cmd)

	def cmdNop(self, cmd):
		if self.debug:
			print "cmd=%0x cmdNop" % ord(cmd)

	# XXX
	def cmdTerm(self, cmd):
		if self.debug:
			print "cmd=%0x cmdTerm" % ord(cmd)

	def cmdDWInit(self, cmd):
		clientID = self.conn.read(1, self.timeout)
		if self.debug:
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
		self.conn.write(t)
		if self.debug:
			print "cmd=%0x cmdTime %s" % (ord(cmd), time.ctime())
		
	def cmdSerSetStat(self, cmd):
		channel = self.conn.read(1, self.timeout)
		if not channel:
			print("cmd=%0x cmdSerSetStat timeout getting channel" % (ord(cmd)))
			return
		#if channel not in self.channels:
		#	print("cmd=%0x cmdSerSetStat bad channel=%d" % (ord(cmd),ord(channel)))
		#	return
		code = self.conn.read(1, self.timeout)
		if not code:
			print("cmd=%0x cmdSerSetStat channel=%d timeout getting code" % (ord(cmd),ord(channel)))
			return
		data = ''
		if code == SS_Open:
			self.channels[channel] = DWVModem(self, channel, debug=self.debug)
			if self.debug:
				print("cmd=%0x SS_Open channel=%d" % (ord(cmd),ord(channel)))
		if code == SS_ComSt:
			data = self.conn.read(26, self.timeout)
		if channel not in self.channels:
			print("cmd=%0x cmdSerSetStat bad channel=%d code=%0x" % (ord(cmd),ord(channel),ord(code)))
		#	return
		elif code == SS_Close:
			#del self.channels[channel]
			self.channels[channel].close()
			if self.debug:
				print("cmd=%0x SS_Close channel=%d" % (ord(cmd),ord(channel)))
		if self.debug:
			print("cmd=%0x cmdSerSetStat channel=%d code=%0x len=%d" % (ord(cmd),ord(channel), ord(code), len(data)))

	def cmdSerGetStat(self, cmd):
		channel = self.conn.read(1, self.timeout)
		if not channel:
			print("cmd=%0x cmdSerGetStat timeout getting channel" % (ord(cmd)))
			return
		if channel not in self.channels:
			print("cmd=%0x cmdSerGetStat bad channel=%d" % (ord(cmd),ord(channel)))
			return
		code = self.conn.read(1, self.timeout)
		if not code:
			print("cmd=%0x cmdSerGetStat channel=%d timeout getting code" % (ord(cmd),ord(channel)))
			return
		if self.debug:
			print("cmd=%0x cmdSerGetStat channel=%d code=%0x" % (ord(cmd),ord(channel), ord(code)))

	def cmdSerInit(self, cmd):
		channel = self.conn.read(1, self.timeout)
		if not channel:
			print("cmd=%0x cmdSerInit timeout getting channel" % (ord(cmd)))
			return
		if channel in self.channels:
			print("cmd=%0x cmdSerInit existing channel=%d" % (ord(cmd),ord(channel)))
			return
		self.channels[channel] = DWVModem(self, channel, debug=self.debug)
		if self.debug:
			print("cmd=%0x cmdSerInit channel=%d" % (ord(cmd),ord(channel)))

	def cmdSerTerm(self, cmd):
		channel = self.conn.read(1, self.timeout)
		if not channel:
			print("cmd=%0x cmdSerTerm timout getting channel" % (ord(cmd)))
			return
		if channel not in self.channels:
			print("cmd=%0x cmdSerTerm bad channel=%d" % (ord(cmd),ord(channel)))
			return
		self.channels[channel].close()
		del self.channels[channel]
		if self.debug:
			print("cmd=%0x cmdSerTerm channel=%d" % (ord(cmd),ord(channel)))

	def cmdFastWrite(self, cmd):
		channel = chr(ord(cmd)-0x80)
		if channel not in self.channels:
			print("cmd=%0x cmdFastWrite bad channel=%d" % (ord(cmd),ord(channel)))
			return
		byte = self.conn.read(1, self.timeout)
		if not byte:
			print("cmd=%0x cmdFastWrite channel=%d timeout" % (ord(cmd),ord(channel)))
			return
		self.channels[channel].write(byte)
		self.channels[channel]._cmdWorker()
		if self.debug:
			print("cmd=%0x cmdFastWrite channel=%d byte=%0x" % (ord(cmd),ord(channel),ord(byte)))

	def cmdSerReadM(self, cmd):
		channel = self.conn.read(1, self.timeout)
		if not channel:
			print("cmd=%0x cmdSerReadM timout getting channel" % (ord(cmd)))
			return
		if channel not in self.channels:
			print("cmd=%0x cmdSerReadM bad channel=%d" % (ord(cmd),ord(channel)))
			return
		num = self.conn.read(1, self.timeout)
		if not num:
			print("cmd=%0x cmdSerReadM channel=%d timeout getting count" % (ord(cmd),ord(channel)))
			return
		data = self.channels[channel].read(ord(num))
		self.conn.write(data)	
		if self.debug:
			print("cmd=%0x cmdSerReadM channel=%d num=%d" % (ord(cmd),ord(channel), ord(num)))

	def cmdSerWriteM(self, cmd):
		channel = self.conn.read(1, self.timeout)
		if not channel:
			print("cmd=%0x cmdSerWriteM timout getting channel" % (ord(cmd)))
			return
		if channel not in self.channels:
			print("cmd=%0x cmdSerWriteM bad channel=%d" % (ord(cmd),ord(channel)))
			return
		num = self.conn.read(1, self.timeout)
		if not num:
			print("cmd=%0x cmdSerWriteM channel=%d timeout getting count" % (ord(cmd),ord(channel)))
			return
		data = self.conn.read(ord(num), self.timeout)
		self.channels[channel].write(data)
		if self.debug:
			print("cmd=%0x cmdSerWriteM channel=%d num=%d" % (ord(cmd),ord(channel), ord(num)))
		self.channels[channel]._cmdWorker()

	def cmdSerWrite(self, cmd):
		channel = self.conn.read(1, self.timeout)
		if not channel:
			print("cmd=%0x cmdSerWrite timout getting channel" % (ord(cmd)))
			return
		if channel not in self.channels:
			print("cmd=%0x cmdSerWrite bad channel=%d" % (ord(cmd),ord(channel)))
			return
		byte = self.conn.read(1, self.timeout)
		if not byte:
			print("cmd=%0x cmdSerWrite channel=%d timeout getting byte" % (ord(cmd),ord(channel)))
			return
		self.channels[channel].write(byte)
		if self.debug:
			print("cmd=%0x cmdSerWrite channel=%d byte=%0x" % (ord(cmd),ord(channel),ord(byte)))
		self.channels[channel]._cmdWorker()

	def cmdPrint(self, cmd):
		data = self.conn.read(1, self.timeout)
		if self.vprinter:
			self.vprinter.write(data)
		if self.debug:
			print("cmd=%0x cmdPrint byte=%0x" % (ord(cmd),ord(data)))

	def cmdPrintFlush(self, cmd):
		if self.vprinter:
			self.vprinter.printFlush()
		if self.debug:
			print("cmd=%0x cmdPrintFlush" % (ord(cmd)))

	def cmdErr(self, cmd):
		print("cmd=%0x cmdErr" % ord(cmd))
		#raise Exception("cmd=%0x cmdErr" % ord(cmd))

        ### EmCee Server ###
        def _emCeeLoadFile(self, filnum, fname, fmode, ftyp=0, opn=False, error=0):
            address = 0
            size = 0
            checksum = 0
            if not error:
                try:
                    fname = self.emCeeAliases.get(fname.upper(), fname)
                    self.files[filnum] = CocoCas(fname, fmode)
                    self.files[filnum].seek()
                    #self.files[filnum] = MlFileReader(fname, fmode, ftyp)
                    #if ftyp == 2: # ml file
                    #        self.files[filnum].readHeader()
                    #        address = self.files[filnum].addr
                    #        size = self.files[filnum]#.
                except:
                    error = E_MC_IO
            if not error:
                try:
                    data = self.files[filnum].read(temp=True)
                    stat = self.files[filnum].stat()
                    size = stat['blk']['blklen']
                    address = stat['nf']['current']
                    #length = min(SECSIZ, self.files[filnum].length)
                    #data = self.files[filnum].tempRead(length)
                    if data:
                        checksum = unpack(">H", dwCrc16(data))[0]
                    else:
                        error = E_MC_IO
                except:
                    error = E_MC_IO
            if error:
                checksum = error
            if opn:
                response = chr(error)
            else:
                response = pack(">HHH", address, size, checksum)
            self.conn.write(response)
            return error

        def _emCeeSaveFile(self, filnum, name, mode, exaddr, size, error):
            if not error:
                name = self.emCeeAliases.get(name.upper(), name)
           	self.files[filnum] = CocoCas(name, 'wb')
		load = start = ascflg = 0 
		ascflg = 0xff	
		if mode == 2:
			load = size
			start = exaddr
			filetype = 2 # ml
			ascflg = 0
		elif mode == 0:
			filetype = 0 # basic
			ascflg = 0 # basic
		else:
			filetype = 1 # data
		nf = CocoCasNameFile(
			filename = name.split(os.path.sep)[-1].split('.')[0][:8].upper(),
			filetype = filetype,
			ascflg = ascflg,
			gap = 1,
			load = load,
			start = start,
		 )
		nfblk = CocoCasBlock(nf.getBlockData(), blktyp=0) # namefile
		self.files[filnum].nf = nf
		self.files[filnum].writeBlock(nfblk)
	    self.conn.write(chr(error))
            return error


        def cmdEmCeeLoadFile(self, cmd):
            error = 0
            info = self.conn.read(2, self.timeout)
            if not info:
                print("cmd=%0x cmdEmCeeLoadFile timout getting command info" % (ord(cmd)))
                error = E_MC_IO # IO ERROR
            if not error:
                ftyp = ord(info[0])
                fnamelen = ord(info[1])
                fname = self.conn.read(fnamelen, self.timeout)
                if not fname:
                    print("cmd=%0x cmdEmCeeLoadFile timout getting file name" % (ord(cmd)))
                    error = E_MC_FN
            if not error:
                error = self._emCeeLoadFile(0, fname, 'rb', ftyp)
            if error:
		print("cmd=%0x cmdEmCeeLoadFile error=%d" % (ord(cmd), error))
                return
            elif self.debug:
		print("cmd=%0x cmdEmCeeLoadFile" % ord(cmd))

        def cmdEmCeeOpenFile(self, cmd):
            fmodes = {
                    1: 'rb',
                    2: 'wb+',
                    3: 'ab+',
            }
            error = 0
            info = self.conn.read(2, self.timeout)
            if not info:
                print("cmd=%0x cmdEmCeeLoadFile timout getting command info" % (ord(cmd)))
                error = E_MC_IO # IO ERROR
            if not error:
                finfo = ord(info[0])
                filnum = finfo & 0x0f
                fmode = fmodes[((finfo & 0xc0)>>6)]
                fnamelen = ord(info[1])
                fname = self.conn.read(fnamelen, self.timeout)
                if not fname:
                    print("cmd=%0x cmdEmCeeLoadFile timout getting file name" % (ord(cmd)))
                    error = E_MC_FN
            if fmode.startswith('r'):
                error = self._emCeeLoadFile(filnum, fname, fmode, opn=True, error=error)
            else:
                self._emCeeSaveFile(filnum, fname, fmode, 0, 0, error)
            if error:
		print("cmd=%0x cmdEmCeeOpenFile error=%d" % (ord(cmd), error))
                return
            elif self.debug:
		print("cmd=%0x cmdEmCeeOpenFile" % ord(cmd))

        def xxx(self):
            if error:
		print("cmd=%0x cmdEmCeeLoadFile error=%d" % ord(cmd), error)
                return
            elif self.debug:
		print("cmd=%0x cmdEmCeeLoadFile" % ord(cmd))

        def cmdEmCeeGetBlock(self, cmd):
            error = 0
            filnum = self.conn.read(1, self.timeout)
            if not filnum:
                error = E_MC_IO
            if not error:
                data = self.files[ord(filnum)].read()
            if data:
                self.conn.write(data)
            if self.debug:
		print("cmd=%0x cmdEmCeeGetBlock" % ord(cmd))

        def cmdEmCeeNextBlock(self, cmd):
            error = 0
            address = 0
            size = 0
            checksum = 0
            filnum = self.conn.read(1, self.timeout)
            if not filnum:
                error = E_MC_IO
            if not error:
                try:
                    fh = self.files[ord(filnum)]
                    if fh == None:
                        error = E_MC_NO
                except:
                    error = E_MC_DN

            if not error:
                try:
                    data = self.files[ord(filnum)].read(temp=True)
                    stat = self.files[ord(filnum)].stat()
                    if stat['blk']['blktyp'] == 0xff:
                        size = 0
                        address = stat['nf']['start']
                    else:
                        size = stat['blk']['blklen']
                        address = stat['nf']['current']
                        #length = min(SECSIZ, self.files[filnum].length)
                        #data = self.files[filnum].tempRead(length)
                        if data:
                            checksum = unpack(">H", dwCrc16(data))[0]
                        else:
                            error = E_MC_IO + 100
                except:
                    raise
                    error = E_MC_IO + 200

            #if not error:
            #    length = min(SECSIZ, fh.remaining)
            #    if length == 0 and fh.ftyp == 2 and fh.typ != 0xff: # Last block and 
            #                fh.readHeader()
            #    try:
            #        #data = fh.tempRead(length)
            #        data = 
            #        if data:
            #            checksum = dwCrc16(data)
            #        else:
            #            error = E_MC_IO
            #    except:
            #        error = E_MC_IO
            if error:
                checksum = error
            response = pack(">HHH", address, size, checksum)
            self.conn.write(response)
            if error:
		print("cmd=%0x cmdEmCeeNextBlock error=%d" % (ord(cmd), error))
                return
            if self.debug:
		print("cmd=%0x cmdEmCeeNextBlock" % ord(cmd))

        def cmdEmCeeSave(self, cmd):
	    error = 0
	    info = self.conn.read(6, self.timeout)
            if not info:
		error = E_MC_IO
            if not error:
		(mode, nameLength, exaddr, size) = unpack(">BBHH", info)
		name = self.conn.read(nameLength, self.timeout)
            if not name:
		    error = E_MC_IO
            self._emCeeSaveFile(0, name, mode, exaddr, size, error)
            if self.debug:
		print("cmd=%0x cmdEmCeeSave" % ord(cmd))

        def cmdEmCeeWriteBlock(self, cmd):
            error = 0
	    data = ''
            eof = False
            info = self.conn.read(3, self.timeout)
	    if not info:
		error = E_MC_IO
	    if not error:
		(fileNum, size) = unpack(">BH", info)
                print fileNum
                if not self.files[fileNum]:
                    error = E_MC_NO
	    if not error:
		if size == 0:
			eof = True
			self.files[fileNum].writeBlock(CocoCasBlock("\xff\x00\xff\x55"))
			self.files[fileNum].close()
		else:
			data = self.conn.read(size, self.timeout)
			if not data:
				error = E_MC_IO
			if not error:
				i = 0
				while i < len(data):
					j = i + 255
					self.files[fileNum].writeBlock(CocoCasBlock(data[i:j], blktyp=1))
					i = j
	    #if not error:
	    dataCrc = dwCrc16(data)
	    self.conn.write(dataCrc)	
            if self.debug:
		print("cmd=%0x cmdEmCeeWriteBlock" % ord(cmd))

        def _cmdEmCeeDirSendNext(self, error=0):
            length = 0
            if not error:
                if self.emCeeDirIdx >= len(self.emCeeDir):
                    self.emCeeDirIdx = 0
                    self.emCeeDir = []
                    length = 0
                else:
                    length = len(self.emCeeDir[self.emCeeDirIdx])
            self.conn.write(chr(error)+chr(length))

        def cmdEmCeeDirFile(self, cmd):
            error = 0
            flag = 0
            dirNam = os.getcwd()
            try:
                flag = ord(self.conn.read(1, self.timeout))
                length = ord(self.conn.read(1, self.timeout))
            except:
                error = E_MC_IO
            if self.debug:
		print("cmd=%0x cmdEmCeeDirFile flag=%d length=%d" % (ord(cmd), flag, length))
            if not error and length>0:
                try:
                    dirNam = self.conn.read(length, self.timeout)
                except:
                    error = E_MC_IO
            if not error:
                if flag == 0:
                    try:
                        dirNam = self.emCeeAliases.get(dirNam.upper(), dirNam)
                        self.emCeeDir = os.listdir(dirNam)
                        self.emCeeDirIdx = 0
                    except:
                        error = E_MC_NE
                else:
                    self.emCeeDirIdx += 1

            self._cmdEmCeeDirSendNext(error)
            if self.debug:
		print("cmd=%0x cmdEmCeeDirFile" % ord(cmd))

        def cmdEmCeeRetrieveName(self, cmd):
            error = 0
            try:
                length = ord(self.conn.read(1, self.timeout))
            except:
                error = E_MC_IO
            if not error:
                dirName = self.emCeeDir[self.emCeeDirIdx][:length]
                self.conn.write(dirName)
            if self.debug:
		print("cmd=%0x cmdEmCeeRetrieveName" % ord(cmd))

        def cmdEmCeeDirName(self, cmd):
            error = 0
            try:
                flag = ord(self.conn.read(1, self.timeout))
                _ = ord(self.conn.read(1, self.timeout))
            except:
                error = E_MC_IO
            if not error:
                if flag == 0:
                    self.emCeeDirIdx = 0
                else:
                    self.emCeeDirIdx += 1

            self._cmdEmCeeDirSendNext(error)
            if self.debug:
		print("cmd=%0x cmdEmCeeDirName" % ord(cmd))

        def cmdEmCeeSetDir(self, cmd):
            error = 0
            try:
                _ = self.conn.read(1, self.timeout)
                length = ord(self.conn.read(1, self.timeout))
            except:
                error = E_MC_IO
            if not error:
                try:
                    dirNam = self.conn.read(length, self.timeout)
                except:
                    raise
                    error = E_MC_IO
            if not error:
                try:
                    dirNam = self.emCeeAliases.get(dirNam.upper(), dirNam)
                    os.chdir(dirNam)
                except:
                    error = E_MC_NE
            self.conn.write(chr(error))
            if self.debug:
		print("cmd=%0x cmdEmCeeSetDir" % ord(cmd))

        def cmdEmCeeErr(self, cmd):
            if self.debug:
		print("cmd=%0x cmdEmCeeErr" % ord(cmd))

	# EmCee Command jump table
        mccommand = {
                MC_LOAD: cmdEmCeeLoadFile,
                MC_GETBLK: cmdEmCeeGetBlock,
                MC_NXTBLK: cmdEmCeeNextBlock,
                MC_SAVE: cmdEmCeeSave,
                MC_WRBLK: cmdEmCeeWriteBlock,
                MC_OPEN: cmdEmCeeOpenFile,
                MC_DIRFIL: cmdEmCeeDirFile,
                MC_RETNAM: cmdEmCeeRetrieveName,
                MC_DIRNAM: cmdEmCeeDirName,
                MC_SETDIR: cmdEmCeeSetDir,
                MC_REWRBLK: cmdEmCeeWriteBlock,
        }

        def doEmCeeCmd(self, cmd):
            mccmd = self.conn.read(1)
            if mccmd:
                try:
                    f=DWServer.mccommand[mccmd]
                except:
                    f= lambda s,x: DWServer.mcErr(s,x)
                f(self, mccmd)

	# DriveWire Command jump table
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
		OP_REWRITE: cmdReWrite,
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
		OP_FASTWRITE2: cmdFastWrite,
		OP_FASTWRITE3: cmdFastWrite,
		OP_FASTWRITE4: cmdFastWrite,
		OP_FASTWRITE5: cmdFastWrite,
		OP_FASTWRITE6: cmdFastWrite,
		OP_FASTWRITE7: cmdFastWrite,
		OP_FASTWRITE8: cmdFastWrite,
		OP_FASTWRITE9: cmdFastWrite,
		OP_FASTWRITE10: cmdFastWrite,
		OP_FASTWRITE11: cmdFastWrite,
		OP_FASTWRITE12: cmdFastWrite,
		OP_FASTWRITE13: cmdFastWrite,
		OP_SERREADM: cmdSerReadM,
		OP_SERWRITE: cmdSerWrite,
		OP_SERWRITEM: cmdSerWriteM,
		OP_PRINT: cmdPrint,
		OP_PRINTFLUSH: cmdPrintFlush,
		MC_ATTENTION: doEmCeeCmd,
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

