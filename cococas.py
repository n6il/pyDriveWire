import re
from struct import *
import tempfile
import urllib

LEADER = '\x55' * 128

class CocoCasNameFile:
    filename = 'FILE    '
    filetype = 0
    ascflg = 0xff
    gap = 1
    start = 0
    load = 0
    current = load
    def __init__(self, data=None, filename=None, filetype=None, ascflg=None, gap=None, start=None, load=None):
	if data is not None:
		(self.filename,
		 self.filetype,
		 self.ascflg,
		 self.gap,
		 self.start,
		 self.load ) = unpack(">8sBBBHH", data)
	else:
		self.filename = filename.ljust(8)
		self.filetype = filetype
		self.ascflg = ascflg
		self.gap = gap
		self.start = start
		self.load = load
		
	self.current = self.load

    def update(self, blk):
        if blk.blktyp == 1:
            self.current += blk.blklen

    def getBlockData(self):
        return pack (">8sBBBHH", 
         self.filename,
         self.filetype,
         self.ascflg,
         self.gap,
         self.start,
         self.load
	)
    def __repr__(self):
        # Namefile block
        filetypes = {
        0: '0(BASIC)',
        1: '1(Data)',
        2: '2(ML)',
        }
        asciiflg = {
        255: 'A',
        0: 'B',
        }
        return "NameFile block: % 8s %s %s" % (self.filename, filetypes[self.filetype], asciiflg[self.ascflg])



class CocoCasBlock:
    blktyp = 0xff
    blklen = 0
    blkcsum = 0xff
    blkdata = ''
    def __init__(self, data, blktyp = None):
        #if not data:
        #    data = "\xff\x00\xff\x55"
	if blktyp is None:
		if len(data) < 4:
		    raise Exception("Short block min=4 len=%d'" % (len(data)))
		if data[-1] != '\x55':
		    raise Exception("Bad block trailer, should be 'U' got '%c'" % data[-1])
		(self.blktyp, self.blklen) = unpack("BB", data[0:2])
		if self.blktyp not in [0,1,255]:
		    raise Exception("Bad block type %d" % self.blktyp)
		self.blkdata = data[2:2+self.blklen]
		(self.blkcsum) = unpack("B", data[2+self.blklen])[0]
	else:
		self.blkdata = data
		self.blktyp = blktyp
		self.blklen = len(data)
		csumData = pack("BB%ds" % (self.blklen), self.blktyp, self.blklen, self.blkdata)
		self.blkcsum = sum(bytearray(csumData))&0xff
    def getBlock(self):
	return  pack("BB%dsBc" % (self.blklen), self.blktyp, self.blklen, self.blkdata, self.blkcsum, 'U')
    def __repr__(self):
            return "blktyp=%d blklen=%d blkcsum=%d" %  (self.blktyp, self.blklen, self.blkcsum)

class CocoCas:
    def __init__(self, fn, mode='rb'):
	self.name = fn
        fn = self.checkWeb(fn)
        self.wav = fn.lower().endswith('wav')
        if self.wav:
            self.file = CocoWavFile()
            self.file.open(fn, mode)
        else:
            self.file = open(fn, mode)
        if mode.startswith('w'):
            self.segments = []
        else:
            self.segments = self.file.read().split('U<')
        self.fn = fn
        self.mode = mode
        self.segment = 0
        self.blk = None
        self.nameFile = None
	self.remote = False

    def checkWeb(self, fileName):
        try:
            #print self.name
            n = self.name.index(':')
            fileName = tempfile.mktemp(prefix=self.name.split('/')[-1].split('.')[0], suffix='.'+self.name.split('.')[-1])
            print("Downloading: %s" % (self.name))
            urllib.urlretrieve(self.name, fileName)
            self.remote = True
        except ValueError:
            pass
        return fileName

    def rewind(self):
        self.segment = 0

    def seek(self, fileName=None):
        found = False
        while not found:
            self.blk = self.readBlk()
            if self.blk.blktyp == 0xff:
                # self.nameFile = CocoCasNameFile(self.blk.blkdata)
                return found
            if self.blk.blktyp == 0:
                nameFile = CocoCasNameFile(self.blk.blkdata)
                if fileName:
                    found = (nameFile.filename == fileName)
                else:
                    found = True
        if found:
                self.nameFile = nameFile
        return found

    def readBlk(self, temp=False):
        if self.segment == len(self.segments):
            segment = "\xff\x00\xff\x55"
        # skip the first segment: it's a leader or empty(no leader)
        if re.match('^U*$', self.segments[self.segment]):
            self.segment += 1
        # fix splitting that may end with a leader
        segment = re.sub('UU*$', 'U', self.segments[self.segment])
        self.blk =  CocoCasBlock(segment)
        if not temp and self.blk.blktyp != 0xff:
            self.segment += 1
        return self.blk

    def read(self, temp=False):
        if not temp and self.nameFile and self.blk:
            self.nameFile.update(self.blk)
        self.readBlk(temp)
        return self.blk.blkdata

    def writeBlock(self, blk):
	if blk.blktyp == 0:
            if self.wav:
                self.file.writeBlank(0.5)
                self.file.write(LEADER)
                self.file.writeBlank(0.003)
                self.file.write('U<')
		self.file.write(blk.getBlock())
                self.file.writeBlank(0.5)
                self.file.write(LEADER)
            else:
		self.segments.append(LEADER)
		self.segments.append(blk.getBlock() + LEADER)
		self.segment += 2
	else:
            if self.wav:
                self.file.writeBlank(0.003)
                self.file.write('U<')
		self.file.write(blk.getBlock())
            else:
		self.segments.append(blk.getBlock())
		self.segment += 1

    def close(self):
	if self.mode.startswith('w'):
            if not self.wav:
                self.file.seek(0)
                self.file.write('U<'.join(self.segments))
                self.file.flush()
            self.file.close()

    def stat(self):
        stat = {}
        nf = self.nameFile
        if nf:
            stat['nf'] = {}
            stat['nf']['load'] = nf.load
            stat['nf']['start'] = nf.start
            stat['nf']['current'] = nf.current
        blk = self.blk 
        if blk:
            stat['blk'] = {}
            stat['blk']['blklen'] = blk.blklen
            stat['blk']['blktyp'] = blk.blktyp
            stat['blk']['blkcsum'] = blk.blkcsum
        return stat

    def _getblock(self, data):
        (blktyp, blklen) = unpack("BB", segment[0:2])
        (checksum) = unpack("BB", segment[2+blklen])

    def __iter__(self):
        self.segment = 0
        # skip the first segment: it's a leader or empty(no leader)
        if re.match('^U*$', self.segments[self.segment]):
            self.segment += 1
        # first segment has to be the name file
        segment = self.segments[self.segment]
        return self

    def __next__(self):
        if self.segment == len(segments):
                raise StopIteration
        
        self.segment += 1


import wave
from struct import *
import math

packDict = {
        1: ">B",
        2: ">H",
}

STATE_START = -1
STATE_ZERO = 0
STATE_RISING = 1
STATE_FALLING = 2
STATE_CROSS = 3
STATE_SAME = 4

states = {
        -1: 'STATE_START',
         0: 'STATE_ZERO',
         1: 'STATE_RISING',
         2: 'STATE_FALLING',
         3: 'STATE_CROSS',
         4: 'STATE_SAME',
         }


class CocoWavFile:
    def open(self, fn, mode='rb', framerate=44100, sampwidth=1, nchannels=1):
        self.w = wave.open(fn, mode)
        if mode.startswith('r'):
            (
                self.nchannels,
                self.sampwidth,
                self.framerate,
                self.nframes,
                self.comptype,
                self.compname,
            ) = self.w.getparams()
        else:
            self.nchannels = nchannels
            self.sampwidth = sampwidth
            self.framerate = framerate
            self.nframes = 0
            self.comptype = 'NONE'
            self.compname = 'NONE'
            self.w.setparams ((
                self.nchannels,
                self.sampwidth,
                self.framerate,
                self.nframes,
                self.comptype,
                self.compname,
            ))

        self.nReadFrames = self.framerate/1200
        self.nbits = self.sampwidth*8
        self.zeroval = 2**(self.nbits-1)
        self.state = STATE_START
        self.prevState = None
        self.prev = chr(self.zeroval)

        if mode.startswith('w'):
            self.genWavTable()


    def genWavTable(self):
        self.wavTable = []
#        for f in [1200, 2400]:
        #for f in [1094.68085106384, 2004.54545454545]:
        for f in [1125, 2250]:
            wavData = ''
            count = int(round(self.framerate/f))
            step = 2*math.pi/count
            theta = 0.0 # step
            for i in range(count):
                val = (128 + (96 * math.sin(theta)))
                #print theta, val
                wavData += chr(int(round(val)))
                theta += step
            self.wavTable.append(wavData)

    def atoi(self, n):
        #print "n=%s" % n
        #return unpack(packDict[sampwidth], n)[0]
        if len(n) == 2:
            return ord(n[0])*256+ord(n[1])
        if len(n) == 1:
            return ord(n)

    def isZero(self,z):
        zl = self.zeroval - 2
        zh = self.zeroval + 2
        return self.atoi(z)>zl and self.atoi(z)<zh


    def getByte(self):
        if self.w.tell() == self.nframes:
            return ''
        byte = 0
        #for i in range(7,-1,-1):
        for i in range(8):
            bit = self.getBit()
            if bit == None:
                return ''
            byte |= (2**i)*bit
            #byte = byte << 1
        #print byte
        return chr(byte)

    def stateChange(self, s, ch):
        #print "State Change: %s -> %s: %d" % (states[state], states[s], ord(ch))
        self.prevState = self.state
        self.state = s

    def getBit(self):
        #self.prev = chr(self.zeroval)
        self.prevState = STATE_START
        self.state = STATE_START
        bit = None
        start = None
        cross1 = None
        end = None
        while start is None or end is None or cross1 is None:
            #for i in range(nReadFrames): # No more than required to get a bit
            char = self.w.readframes(1)
            if char == '':
                return None
            #print "char=%s p=%s" % (char, prev)
            ci = self.atoi(char)
            pi = self.atoi(self.prev)
            #print "ci=%s pi=%s" % (ci, pi)
            if start is None and self.isZero(char):
                self.stateChange(STATE_ZERO,char)
            elif pi < self.zeroval-1 and ci >= self.zeroval-1:
                self.stateChange(STATE_CROSS,char)
            elif pi > self.zeroval+1 and ci <= self.zeroval+1:
                self.stateChange(STATE_CROSS,char)
            elif pi == ci:
                self.stateChange( STATE_SAME, char)
            elif ci > pi:
                self.stateChange ( STATE_RISING, char)
            elif ci < pi:
                self.stateChange ( STATE_FALLING, char)
            self.prev = char
            if self.prevState in [STATE_START, STATE_ZERO] and self.state in [STATE_RISING, STATE_FALLING] and start is None:
                start = self.w.tell()
            elif self.prevState in [STATE_RISING, STATE_FALLING] and self.state in [STATE_CROSS]:
                if cross1 is None:
                    cross1 = self.w.tell()
                elif end is None:
                    end = self.w.tell()
            #elif prevState in [STATE_RISING, STATE_FALLING] and state in [STATE_ZERO]:
            #    end = w.tell()
        #print "start=%s cross1=%s end=%s" % (start ,cross1, end)
        cycles = end - start
        bit = cycles > (self.nReadFrames/2*1.2)
        #print " ",cycles,bit
        if bit:
            return 0
        else:
            return 1


    def passLeader(self, w):
     b = 'U'
     while b=='U':
         b=self, getByte(w)
         print b
     return b

    def read(self, count=None):
        data = ''
        #w = wave.open(fn)
        read = 0
        b='\x00'
        while b != '':
            b = self.getByte()
            data += b
            read += 1
            if count and count==read:
                break
        return data

    def writeByte(self, c):
            ci = ord(c)
            for i in range(8):
                bit = (ci >> i) & 1
                self.w.writeframes(self.wavTable[bit])

    def write(self, data):
        for c in data:
            self.writeByte(c)

    def writeBlank(self, s):
        nframes = int(round(self.framerate*s))
        zeroData = nframes * chr(self.zeroval)
        self.w.writeframes(zeroData)

    def close(self):
        self.w.close()
        self.w = None
