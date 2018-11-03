import re
from struct import *

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
		self.segments.append(LEADER)
		self.segments.append(blk.getBlock() + LEADER)
		self.segment += 2
	else:
		self.segments.append(blk.getBlock())
		self.segment += 1

    def close(self):
	if self.mode.startswith('w'):
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
