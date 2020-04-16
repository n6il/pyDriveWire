# !/usr/bin/python

import sys
import os
from os import stat
from struct import *
import tempfile
import urllib
from urlparse import urlparse
from urllib2 import Request, urlopen

COCO_SECTOR_SIZE = 256
COCO_DEFAULT_DISK_SIZE = 630

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
    def __init__(self, name, mode='r', typ=None, stream=False):
        self.name = name
        self.mode = mode
        self.remote = False
        self.fmt = formats[COCO_DEFAULT_DISK_SIZE]
        self.maxLsn = self.fmt['sides'] * \
            self.fmt['tracks'] * self.fmt['sectors']
        self.stream = stream
        self._doOpen()
        if not self.stream:
            try:
                self.guessMaxLsn()
            except:
                pass
        self.os9Image = False
        self.offset = 0

    def _delete(self):
        print("Deleting temporary file: %s" % self.file.name)
        os.unlink(self.file.name)

    def _doOpen(self):
        fileName = self.name
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
        self.file = open(fileName, self.mode)

    def guessMaxLsn(self, data=None):
        self.fmt = self._os9Fmt(data)
        if self.fmt:
            self.os9Image = True
        else:
            # if sectors == 0 and st.st_size > 0:
            #    sectors = COCO_DEFAULT_DISK_SIZE
            self.os9Image = False
            st = stat(self.file.name)
            img_size = st.st_size
            sectors = img_size / COCO_SECTOR_SIZE
            self.fmt = self._fmtSearch(sectors)

        self.maxLsn = self.fmt['sides'] * \
            self.fmt['tracks'] * self.fmt['sectors']
        # print "%s: %d %s" % (self, self.maxLsn, self.fmt['descr'])

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
    print ("Image File Info::")
    print ("Img File: %s" % dwf.name)
    print ("Img Total Sectors: %d" % dwf.maxLsn)
    print (" ")
    print ("Detected disk format::")
    print ("%s" % fmt['descr'])
    print ("Sectors: %d" % fmt['sectors'])
    print ("Tracks: %d" % fmt['tracks'])
    print ("Sides: %d" % fmt['sides'])
    print ("Bytes/Sector: %d" % fmt['bytes'])


# vim: ts=4 sw=4 sts=4 expandtab
