# !/usr/bin/python

import sys
import os
from os import stat
from struct import *
import tempfile
import urllib
from urlparse import urlparse
from urllib2 import Request, urlopen
import re

COCO_SECTOR_SIZE = 256
COCO_DEFAULT_DISK_SIZE = 630
COCO_HDBDOS_NUMDISKS = 256
COCO_SECTORS_PER_TRACK = 18

formats = {
    630: {'sides': 1, 'tracks': 35, 'sectors': 18, 'bytes': COCO_SECTOR_SIZE, 'descr': 'CoCo Standard 160K: Single-Sided, 35 Track, 18-Sectors/Track, 256Byte/Sector Image'},
    720: {'sides': 1, 'tracks': 40, 'sectors': 18, 'bytes': COCO_SECTOR_SIZE, 'descr': 'CoCo 180K: Single-Sided, 40 Track, 18-Sectors/Track, 256Byte/Sector Image'},
    # 1260 : {'sides': 2, 'tracks': 35, 'sectors': 18, 'bytes':
    # COCO_SECTOR_SIZE, 'descr': 'CoCo 320K: Double-Sided, 35 Track,
    # 18-Sectors/Track, 256Byte/Sector Image' },
    1440: {'sides': 2, 'tracks': 40, 'sectors': 18, 'bytes': COCO_SECTOR_SIZE, 'descr': 'CoCo 360K: Double-Sided, 40 Track, 18-Sectors/Track, 256Byte/Sector Image'},
    2880: {'sides': 2, 'tracks': 80, 'sectors': 18, 'bytes': COCO_SECTOR_SIZE, 'descr': 'CoCo 720K: Double-Sided, 80 Track, 18-Sectors/Track, 256Byte/Sector Image'},
}


class DWFile:
    def __init__(self, name, mode='r', typ=None, stream=False, offset=0, raw=False, eolxlate=False, proto='dw'):
        self.name = name
        self.mode = mode
        self.remote = False
        self.fmt = formats[COCO_DEFAULT_DISK_SIZE]
        self.maxLsn = self.fmt['sides'] * \
            self.fmt['tracks'] * self.fmt['sectors']
        self.stream = stream
        self.raw = raw
        self.eolxlate = eolxlate
        self.proto = proto
        self._doOpen()
        self.os9Image = False
        self.offset = offset
        self.byte_offset = 0
        if not self.stream:
            try:
                self.guessMaxLsn()
            except BaseException:
                pass

    def _delete(self):
        print("Deleting temporary file: %s" % self.file.name)
        os.unlink(self.file.name)

    def _doOpen(self):
        fileName = os.path.expanduser(self.name)
        if self.stream:
            self.remote = True
            print("Enabling streaming mode for %s" % fileName)
            self.file = DwHttpStreamingFile(fileName, ssize=COCO_SECTOR_SIZE)
            return
        try:
            # print self.name
            pp = urlparse(self.name)
            if pp[0].lower() in ['http', 'https', 'ftp']:
                fileName = tempfile.mktemp(prefix=self.name.split(
                    '/')[-1].split('.')[0], suffix='.' + self.name.split('.')[-1])
                print("Downloading: %s" % (self.name))
                urllib.urlretrieve(self.name, fileName)
                self.remote = True
        except ValueError:
            pass
        except BaseException:
            raise
        if self.eolxlate:
            print("Opening %s with file translation" % (fileName))
            fn = tempfile.mktemp(prefix=os.path.basename(fileName))
            print("Temp file: %s" % (fn))
            self.file = open(fn, 'w+', buffering=0)
            with open(fileName) as f:
                fdata = f.read()
                (new, n) = re.subn('\x0d\x0a', '\x0d',  fdata)
                if n:
                    fdata = new
                (new, n) = re.subn('\x0a', '\x0d',  fdata)
                if n:
                    fdata = new
            self.file.write(fdata)
            self.file.seek(0)
        else:
            self.file = open(fileName, self.mode, buffering=0)


    def guessMaxLsn(self, data=None):
        st = stat(self.file.name)
        self.img_size = st.st_size
        self.img_sectors = self.img_size / COCO_SECTOR_SIZE
        self.fmt = None
        if self.raw:
            return
        fmt = self._vdkFmt()
        if fmt:
            self.fmt = fmt
            self.img_sectors -= 1
            self.os9Image = False
        if not self.fmt:
            fmt = self._jvcFmt()
            if fmt:
                self.fmt = fmt
                self.img_size = (self.fmt['sides'] * self.fmt['tracks'] * self.fmt['sectors'] * self.fmt['bytes'])
                self.os9Image = False

        if not self.fmt:
            fmt = self._os9Fmt(data)
            if fmt:
                #if self.fmt:
                #    fmt.byte_offset = self.fmt['byte_offset']
                self.fmt = fmt
                self.os9Image = True
        if not self.fmt:
            # if sectors == 0 and st.st_size > 0:
            #    sectors = COCO_DEFAULT_DISK_SIZE
            fmt = self._fmtSearch(self.img_sectors)
            #if self.fmt:
                #fmt.byte_offset = self.fmt['byte_offset']
            self.fmt = fmt
            self.os9Image = False

        self.maxLsn = self.fmt['sides'] * \
            self.fmt['tracks'] * self.fmt['sectors']
        # print "%s: %d %s" % (self, self.maxLsn, self.fmt['descr'])
        if self.maxLsn < self.img_sectors:
            hdb_img_sec = COCO_DEFAULT_DISK_SIZE * COCO_HDBDOS_NUMDISKS
            if self.os9Image:
                # Let the disk image grow to the os9 partition size + hdb_img size
                # XXX: Do logic here
                # if self.maxLsn == self.img_size:
                # else:
                self.maxLsn = max(self.maxLsn + hdb_img_sec, self.img_sectors)
            else:
                # Let the disk image grow to the os9 partition size + hdb_img size
                self.maxLsn = max([hdb_img_sec, self.img_sectors])

    def _fmtSearch(self, sectors):
        if sectors == 0:
            raise Exception("%s: Zero-length disk image" % self.name)
        fmt = formats.get(sectors, None)
        if fmt:
            # print("%s: %s" % (dsk_img, fmt['descr']))
            return fmt
        # search for the next highest
        fmt = None
        for secs in sorted(formats.keys()):
            if sectors < secs:
                fmt = formats[secs]
                break
        # if fmt:
        #    # Smaller than a standard size so assume it is truncated
        #    real_img_size = fmt['sides'] * fmt['tracks'] * fmt['sectors'] * fmt['bytes']
        #    print("%s: %s Truncated to %s/%s bytes" % (dsk_img, fmt['descr'], st.st_size, real_img_size))

        if not fmt:
            # make a guess
            sides = 1
            spt = 18
            tracks = sectors / spt
            secsiz = COCO_SECTOR_SIZE
            fmt_str = 'Single-Sided, %d Track, %d-Sectors/Track, %dByte/Sector Image' % (
                tracks, spt, secsiz)
            fmt = {
                'sides': sides,
                'tracks': tracks,
                'sectors': spt,
                'bytes': secsiz,
                'descr': fmt_str}
        return fmt

    def _os9Fmt(self, lsn0=None):
        # Larger than a standard floppy so it must be a HDD Image
        # Guess 1: OS-9 Image
        lsn0_offset = 0
        # Guess 2: HDB Dos Image
        # lsn0_offset = COCO_SECTOR_SIZE * COCO_DEFAULT_DISK_SIZE
        if not lsn0:
            oldLoc = self.file.tell()
            self.file.seek(0)
            lsn0 = self.file.read(COCO_SECTOR_SIZE)
            self.file.seek(oldLoc)
        dd_tot = None
        dd_spt = None
        dd_fmt_sides = None
        try:
            dd_tot = unpack(">I", "\x00" + lsn0[0x0:3])[0]
            dd_tks = unpack(">B", lsn0[0x3])[0]
            dd_fmt = unpack(">B", lsn0[0x10])[0]
            dd_fmt_sides = (dd_fmt & 0x01) + 1
            dd_fmt_density = (dd_fmt & 0x02) >> 1
            dd_fmt_tpi = (dd_fmt & 0x04) >> 2
            dd_spt = unpack(">H", lsn0[0x11:0x13])[0]
        except BaseException:
            dd_tot = None

        # fmt = fmtSearch(dd_tot)
        # if fmt:
        #    break

        fmt = None
        if not all([dd_tot, dd_spt, dd_fmt_sides]):
            return fmt
            # raise Exception ("Not a valid OS-9 Image")

        tracks = dd_tot / dd_spt / dd_fmt_sides

        if dd_tks != dd_spt or dd_tot != (tracks * dd_spt * dd_fmt_sides):
            return fmt
            # raise Exception ("Not a valid OS-9 Image")
        # print ("Img Sectors: %d" % sectors)
        # print ("Total Sectors: %d" % dd_tot)
        # print ("Track Size: %d" % dd_tks)
        # print ("Disk Format: %x (%d TPI, %s Density, %s Sided)" % (dd_fmt, 96 if dd_fmt_tpi else 48, "Double" if dd_fmt_density else "Single", "Double" if dd_fmt_sides else "Single"))
        # print ("Tracks: %d" % tracks)
        # print ("Sides: %d" % dd_fmt_sides)
        ks = dd_tot * COCO_SECTOR_SIZE / 1024
        # print ("Size: %dK" % ks)
        fmt_str = "NitrOS-9: %sK, %d Sides, %d tracks, %d-Sectors/Track, 256Byte/Sector Image" % (
            ks, dd_fmt_sides, tracks, dd_spt, )
        # print fmt_str

        fmt = {
            'sides': dd_fmt_sides,
            'tracks': tracks,
            'sectors': dd_spt,
            'bytes': COCO_SECTOR_SIZE,
            'descr': fmt_str}
        # assert(dd_tot == sectors)
        return fmt

    def _vdkFmt(self):
        fmt = None
        self.file.seek(0)
        hdr = self.file.read(2)
        if hdr != 'dk':
            self.file.seek(0)
            return None
        # Byte Offset 	Description
        # 0, 1 	'd', 'k'
        # 2, 3 	Header size (little-endian)
        # 4 	Version of VDK format
        # 5 	Backwards compatibility version
        # 6 	Identity of file source
        # 7 	Version of file source
        # 8 	Number of tracks
        # 9 	Number of sides
        # 10 	Flags
        # 11 	Compression flags and name length
        (
            hsize,
            vdkVer,
            compatibility,
            ident,
            ver,
            tracks,
            sides,
            flags1,
            flags2
            ) = unpack('HBBBBBBBB', self.file.read(10))
        self.byte_offset = hsize
        size = (sides * tracks * COCO_SECTORS_PER_TRACK * COCO_SECTOR_SIZE)
        sizeK = size / 1024
        fmt_str = "%sK, %d Sides, %d tracks, %d-Sectors/Track, 256Byte/Sector VDK Image" % (
               sizeK, sides, tracks,  COCO_SECTORS_PER_TRACK )
        fmt = {
            'sides': sides,
            'tracks': tracks,
            'sectors': COCO_SECTORS_PER_TRACK,
            'bytes': COCO_SECTOR_SIZE,
            'descr': fmt_str,
               }
        self.file.seek(self.byte_offset)
        return fmt

    def _jvcFmt(self):
        fmt = None
        xtrabytes = self.img_size - (self.img_sectors * COCO_SECTOR_SIZE)
        if xtrabytes <= 0:
            return fmt
        self.byte_offset = xtrabytes
        img_realsize = self.img_size - xtrabytes

        spt = 18
        sides = 1
        ssizc = 1
        fsec = 1
        flags = 0
        self.file.seek(0)
        if xtrabytes:
            spt = int(unpack(">B", self.file.read(1))[0])
            xtrabytes -= 1
        if xtrabytes:
            sides = int(unpack(">B", self.file.read(1))[0])
            xtrabytes -= 1
        if xtrabytes:
            ssizc = int(unpack(">B", self.file.read(1))[0])
            xtrabytes -= 1
        if xtrabytes:
            fsec = int(unpack(">B", self.file.read(1))[0])
            xtrabytes -= 1
        if xtrabytes:
            flags = int(unpack(">B", self.file.read(1))[0])
            xtrabytes -= 1

        ssize = 128 * (2**ssizc)
        tracks = img_realsize / ssize / sides / spt
        size = (sides * tracks * spt * ssize)
        sizeK = size / 1024
        fmt_str = "%sK, %d Sides, %d tracks, %d-Sectors/Track, %sByte/Sector JVC Image" % (
               sizeK, sides, tracks,  spt , ssize)
        fmt = {
            'sides': sides,
            'tracks': tracks,
            'sectors': spt,
            'bytes': ssize,
            'descr': fmt_str,
               }
        self.file.seek(self.byte_offset)
        print fmt
        return fmt


    def seek(self, pos):
        if self.fmt:
            sbytes = pos * self.fmt['bytes']
        else:
            sbytes = pos * COCO_SECTOR_SIZE
        if self.byte_offset:
            self.file.seek(self.byte_offset + pos)
        elif self.offset:
            self.file.seek((self.offset * sbytes) + pos)
        else:
            self.file.seek(pos)

    def tell(self):
        pos = self.file.tell()
        if self.fmt:
            sbytes = self.fmt['bytes']
        else:
            sbytes = COCO_SECTOR_SIZE
        if self.byte_offset:
            pos -= self.byte_offset
        if self.offset:
            pos -= self.offset * sbytes
        return pos

class MlFileReader:

    def __init__(self, fileName, mode, ftyp):
        self.fileName = fileName
        self.file = open(fileName, mode)
        self.ftyp = ftyp
        st = stat(fileName)
        self.flength = st.st_size
        self.typ = 0
        self.length = self.flength  # default value for non-ml files
        self.offset = 0
        self.remaining = self.flength  # default value for non-ml files

    def readHeader(self):
        self.offset = self.file.tell()
        data = self.file.read(5)
        (typ, length, addr) = unpack(">BHH", data)
        self.typ = typ
        self.addr = addr
        self.length = length
        self.remaining = length
        return typ

    def read(self, length=None):
        if self.typ == 0xff or self.remaining == 0:
            return ''
        if not length:
            length = self.remaining
        self.remaining -= length
        return self.file.read(length)

    def tempRead(self, length=None):
        prev = self.file.tell()
        if self.typ == 0xff or self.remaining == 0:
            return ''
        if not length:
            length = self.remaining
        data = self.file.read(length)
        self.file.seek(prev)
        return data


class DwHttpStreamingFile:

    def __init__(self, url, pos=0, ssize=256):
        self.url = url
        self.name = url
        self.ssize = ssize
        self.pos = pos

    def seek(self, pos):
        # print("seek", self.name, pos)
        self.pos = pos

    def tell(self):
        # print("tell", self.name, self.pos)
        return self.pos

    def read(self, count):
        # print("read", self.name, self.pos, count)
        start = self.pos
        end = self.pos + count - 1

        req = Request(self.url)
        req.add_header("Range", "bytes=%d-%d" % (start, end))

        content = ''
        uh = urlopen(req)
        if uh.code >= 200 and uh.code < 300:
            content = uh.read()
        else:
            print("%s %d %d" % (self.url, uh.code, len(content)))

        return content

    def write(self, data):
        raise Exception("Write not implemented")

    def flush(self):
        return

    def close(self):
        return


if __name__ == '__main__':
    import sys
    f = sys.argv[1]
    dwf = DWFile(f)
    fmt = dwf.fmt
    print("Image File Info::")
    print("Img File: %s" % dwf.name)
    print("Img Total Sectors: %d" % dwf.maxLsn)
    print(" ")
    print("Detected disk format::")
    print("%s" % fmt['descr'])
    print("Sectors: %d" % fmt['sectors'])
    print("Tracks: %d" % fmt['tracks'])
    print("Sides: %d" % fmt['sides'])
    print("Bytes/Sector: %d" % fmt['bytes'])


# vim: ts=4 sw=4 sts=4 expandtab
