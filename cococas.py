import math
import wave
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

    def __init__(
            self,
            data=None,
            filename=None,
            filetype=None,
            ascflg=None,
            gap=None,
            start=None,
            load=None):
        if data is not None:
            (self.filename,
             self.filetype,
             self.ascflg,
             self.gap,
             self.start,
             self.load) = unpack(">8sBBBHH", data)
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
        return pack(">8sBBBHH",
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
        return "NameFile block: % 8s %s %s" % (
            self.filename, filetypes[self.filetype], asciiflg[self.ascflg])


class CocoCasBlock:
    blktyp = 0xff
    blklen = 0
    blkcsum = 0xff
    blkdata = ''

    def __init__(self, data, blktyp=None):
        # if not data:
        #    data = "\xff\x00\xff\x55"
        if blktyp is None:
            if len(data) < 4:
                raise Exception("Short block min=4 len=%d'" % (len(data)))
            if data[-1] != '\x55':
                raise Exception(
                    "Bad block trailer, should be 'U' got '%c'" % data[-1])
            (self.blktyp, self.blklen) = unpack("BB", data[0:2])
            if self.blktyp not in [0, 1, 255]:
                raise Exception("Bad block type %d" % self.blktyp)
            self.blkdata = data[2:2 + self.blklen]
            (self.blkcsum) = unpack("B", data[2 + self.blklen])[0]
        else:
            self.blkdata = data
            self.blktyp = blktyp
            self.blklen = len(data)
            csumData = pack(
                "BB%ds" %
                (self.blklen),
                self.blktyp,
                self.blklen,
                self.blkdata)
            self.blkcsum = sum(bytearray(csumData)) & 0xff

    def getBlock(self):
        return pack(
            "BB%dsBc" %
            (self.blklen),
            self.blktyp,
            self.blklen,
            self.blkdata,
            self.blkcsum,
            'U')

    def __repr__(self):
        return "blktyp=%d blklen=%d blkcsum=%d" % (
            self.blktyp, self.blklen, self.blkcsum)


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
            segments = self.file.read()
            segments = re.sub('^\x00{5,}', '', segments)
            segments = re.sub('\x00{5,}$', '', segments)
            self.segments = segments.split('U<')
        self.fn = fn
        self.mode = mode
        self.segment = 0
        self.blk = None
        self.nameFile = None
        self.remote = False
        #
        self.offset = 0
        self.raw = True
        self.eolxlate = False
        self.proto = 'mc'

    def checkWeb(self, fileName):
        try:
            # print self.name
            n = self.name.index(':')
            fileName = tempfile.mktemp(prefix=self.name.split(
                '/')[-1].split('.')[0], suffix='.' + self.name.split('.')[-1])
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
        else:
            if re.match('^\x00*U*$', self.segments[self.segment]):
                self.segment += 1
            segment = self.segments[self.segment]
        # fix splitting that may end with a leader
        segment = re.sub('U\x00*U*$', 'U', segment)
        # segment = re.sub('UU*$', 'U', segment)
        self.blk = CocoCasBlock(segment)
        if not temp and self.blk.blktyp != 0xff:
            self.segment += 1
        return self.blk

    def read(self, temp=False):
        if not temp and self.nameFile and self.blk:
            self.nameFile.update(self.blk)
        self.readBlk(temp)
        return self.blk.blkdata

    def writeBlock(self, blk):
        if blk.blktyp in [0, 0xff]:
            if self.wav:
                self.file.writeBlank(0.5)
                self.file.write(LEADER)
                self.file.writeBlank(0.003)
                self.file.write('U<')
                self.file.write(blk.getBlock())
                if blk.blktyp == 0:
                    self.file.writeBlank(0.5)
                    self.file.write(LEADER)
                elif blk.blktyp == 0xff:
                    self.file.writeBlank(0.003)
            else:
                self.segments.append(LEADER)
                blkdata = blk.getBlock()
                if blk.blktyp == 0:
                    blkdata += LEADER
                self.segments.append(blkdata)
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
        (checksum) = unpack("BB", segment[2 + blklen])

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


packDict = {
    1: ">B",
    2: "<h",
}

STATE_START = -1
STATE_ZERO = 0
STATE_FOLLOW = 1
STATE_CROSS = 2

states = {
    -1: 'STATE_START',
    0: 'STATE_ZERO',
    1: 'STATE_FOLLOW',
    2: 'STATE_CROSS',
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
            self.w.setparams((
                self.nchannels,
                self.sampwidth,
                self.framerate,
                self.nframes,
                self.comptype,
                self.compname,
            ))

        self.nReadFrames = self.framerate / 1200
        self.nbits = self.sampwidth * 8
        self.zeroval = 2**(self.nbits - 1) if self.sampwidth == 1 else 0
        self.zero = chr(self.zeroval) if self.sampwidth == 1 else "\x00\x00"
        self.state = STATE_START
        self.prevState = None
        self.prev = self.zero
        # print self.zeroval

        if mode.startswith('w'):
            self.genWavTable()

        self.lol = self.framerate / 1200.0 * 0.7
        self.loh = self.framerate / 1200.0 * 1.3
        self.lohhc = self.loh / 2
        self.hil = self.framerate / 2400.0 * 0.7
        self.hilhc = self.hil / 2
        self.hih = self.framerate / 2400.0 * 1.3
        self.midhc = (self.lohhc + self.hilhc) / 2
        # mid = round((self.lohhc+self.hilhc)/2)
        self.mid = (self.loh + self.hil) / 2
        # print "lol=%s loh=%s hil=%s hih=%s lohhc=%s hilhc=%s" % (self.lol, self.loh, self.hil, self.hih, self.lohhc, self.hilhc)
        self.diff = 2 if self.sampwidth == 1 else 256
        self.zl = self.zeroval - self.diff
        self.zh = self.zeroval + self.diff

    def genWavTable(self):
        self.wavTable = []
        mult = 0.75 * 2**(self.nbits - 1)
#        for f in [1200, 2400]:
        # for f in [1094.68085106384, 2004.54545454545]:
        for f in [1125, 2250]:
            wavData = ''
            count = int(round(self.framerate / f))
            step = 2 * math.pi / count
            theta = 0.0  # step
            for i in range(count):
                val = (self.zeroval + (mult * math.sin(theta)))
                # print theta, val
                wavData += pack(packDict[self.sampwidth], val)
                theta += step
            self.wavTable.append(wavData)

    def atoi(self, n):
        # print "n=%s" % n
        r = unpack(packDict[self.sampwidth], n)[0]
        # print r
        return r

    def isZero(self, z):
        v = self.atoi(z)
        # print zl,v,zh
        return self.atoi(z) > self.zl and self.atoi(z) < self.zh

    def getByte(self):
        if self.w.tell() == self.nframes:
            return ''
        byte = 0
        # for i in range(7,-1,-1):
        for i in range(8):
            bit = self.getBit()
            if bit is None:
                return ''
            byte |= (2**i) * bit
            # byte = byte << 1
        # print byte
        return chr(byte)

    def stateChange(self, s, ch):
        # print "State Change: %s -> %s: %d" % (states[self.state], states[s], self.atoi(ch))
        self.prevState = self.state
        self.state = s

    def getBit(self):
        """
        Software Zero-Crossing Detector


        Use the number of wav file frames between two zero crosses (half of the
        sin wave) to determine the bit.
        """

        start = None
        self.prevState = STATE_START
        self.state = STATE_START
        startpos = self.w.tell()
        end = None
        bit = None

        ncross = 0
        cycles = 0
        while ncross < 1:
            start = end = None
            cross1 = True
            while start is None or end is None:
                char = self.w.readframes(1)
                if char == '':
                    if start:
                        # Got to the end of the file and found a cross before
                        # Slip back to the beginning of the bit check
                        # repeat the last value
                        char = self.prev
                        # end - first cross detected
                        end = start
                        # start - the starting position for this bit check
                        start = startpos
                        continue
                    else:
                        return None
                # print "char=%s p=%s" % (char, self.prev)
                ci = self.atoi(char)
                pi = self.atoi(self.prev)
                # print "ci=%s pi=%s" % (ci, pi)
                if pi < self.zeroval - 1 and ci >= self.zeroval - 1:
                    self.stateChange(STATE_CROSS, char)
                elif pi > self.zeroval + 1 and ci <= self.zeroval + 1:
                    self.stateChange(STATE_CROSS, char)
                else:
                    self.stateChange(STATE_FOLLOW, char)
                self.prev = char

                if self.state == STATE_CROSS:
                    pos = self.w.tell()
                    if not start:
                        start = pos
                    # print "cross: start: start=%s cross1=%s end=%s" % (start ,cross1, end)
                    elif not end:
                        end = pos
                # print "end: start=%s cross1=%s end=%s" % (start ,cross1, end)

            cc = end - start
            # print self.hilhc, cc, self.lohhc
            if (cc > self.lohhc) or (cc < self.hilhc):
                # freqency is out of range
                # skip this one and move to the next pair of zero crosses
                start = end
                end = None
            else:
                cycles += cc
                ncross += 1
                # print "ncross=%s cc=%s cycles=%s" % (ncross, cc, cycles)

        cycles = end - start
        if cycles <= self.midhc:
            bit = 1
        if cycles > self.midhc:
            bit = 0

        # print cycles, bit
        return bit

    def passLeader(self, w):
        b = 'U'
        while b == 'U':
            b = self, getByte(w)
            print b
        return b

    def read(self, count=None):
        data = ''
        # w = wave.open(fn)
        read = 0
        b = '\x00'
        while b != '':
            b = self.getByte()
            data += b
            # if b:
            #   n=ord(b)
            #   c=b if n>=32 and n<128 else '.'
            #   print c,hex(n)
            read += 1
            if count and count == read:
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
        nframes = int(round(self.framerate * s))
        zeroData = nframes * chr(self.zeroval)
        self.w.writeframes(zeroData)

    def close(self):
        self.w.close()
        self.w = None


# vim: ts=4 sw=4 sts=4 expandtab
