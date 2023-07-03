import time
from struct import *
from ctypes import *
import traceback
import os
import re
import sys
import platform

from dwconstants import *
from dwchannel import *
from dwfile import DWFile
from dwutil import *
from dwlib import canonicalize

from cococas import *
import multiprocessing


NULL_SECTOR = NULL * SECSIZ


def _playsound(name, d, block):
    import playsound
    from playsound import playsound
    pwd = os.getcwd()
    os.chdir(d)
    playsound(name, block)
    os.chdir(pwd)


class DWServer:
    def __init__(self, args, conn, version, instances, instance):
        self.conn = conn
        self.files = [None] * 256
        self.channels = {}
        self.connections = {}
        self.debug = False
        self.timeout = 0.25
        self.version = version
        self.vprinter = None

        self.emCeeDir = []
        self.emCeeDirIdx = 0
        if args.experimental:
            if 'printer' in args.experimental:
                print("DWServer: Enabling experimental printing support")
                from dwprinter import DWPrinter
                self.vprinter = DWPrinter(args)
            if 'ssh' in args.experimental:
                print("DWServer: Enabling experimental ssh support")
            if 'playsound' in args.experimental:
                print("DWServer: Enabling experimental playsound support")
                import playsound
                from playsound import playsound
        self.aliases = {'mc':{}, 'dload':{}, 'namedobj': {}, 'playsound':{}}
        self.dirs = {'dw': os.getcwd(), 'mc': os.getcwd(), 'dload': os.getcwd(), 'namedobj': os.getcwd(), 'playsound': os.getcwd() }
        self.instances = instances
        self.instance = instance
        self.hdbdos = args.hdbdos
        self.dosplus = args.dosplus
        self.offset = eval(args.offset)
        self.args = args
        self.dload = False
        self.namedObjDrive = None
        self.comboLock = 0
        self.procs = []

    def _isNamedObjDrive(self, drive):
        if self.namedObjDrive is None:
            return False
        if drive != self.namedObjDrive:
            return False
        if self.files[drive] is None:
            return False
        return True

    def registerConn(self, conn):
        n = None
        i = 0
        si = "1"
        while i <= len(self.connections):
            n = self.connections.get(si, None)
            if not n:
                break
            i += 1
            si = "%d" % (i + 1)
        self.connections[si] = conn
        return si

    def open(self, disk, fileName, stream=False, mode="rb+", create=False, offset=None, hdbdos=None, raw=False, eolxlate=False, proto='dw', dosplus=None):
        if offset is None:
            offset = self.offset
        if hdbdos is None:
            hdbdos = self.hdbdos
        if dosplus is None:
            dosplus = self.dosplus
        if proto in self.dirs:
            print("chdir: %s: %s" % (proto, self.dirs[proto]))
            os.chdir(self.dirs[proto])
        self.files[disk] = DWFile(fileName, mode, stream=stream, offset=offset, raw=raw, eolxlate=eolxlate, proto=proto, dosplus=dosplus)
        print(
            '%s: disk=%d file=%s stream=%s mode=%s' %
            ('Created' if create else 'Opened', disk, fileName, stream, mode))
        self.files[disk].seek(0)
        self.files[disk].hdbdos = hdbdos

    def close(self, disk):
        d = self.files[disk]
        if d and isinstance(d, DWFile):
            name = d.file.name
            print('Closing: disk=%d file=%s' % (disk, d.name))
            d.file.flush()
            os.fsync(d.file.fileno())
            d.file.close()
            if d.remote and not d.stream:
                d._delete()
            if self._isNamedObjDrive(disk):
                self.namedObjDrive = None
        if d:
            self.files[disk] = None

    def closeAll(self):
        for disk in range(len(self.files)):
            if self.files[disk]:
                self.close(disk)

    def reset(self, disk):
        df = self.files[disk]
        fileName = df.name
        stream = df.stream
        mode = df.mode
        offset = df.offset
        hdbdos = df.hdbdos
        dosplus = df.dosplus
        raw = df.raw
        eolxlate = df.eolxlate
        proto = df.proto
        print('Reset: disk=%d file=%s' % (int(disk), fileName))
        self.close(disk)
        self.open(disk, fileName, stream=stream, mode=mode, offset=offset,
            hdbdos=hdbdos, raw=df.raw, eolxlate=eolxlate, proto=proto,
            dosplus=dosplus)

    def cmdStat(self, cmd):
        info = self.conn.read(STATSIZ, self.timeout)
        if not info:
            print "cmd=%0x cmdStat timeout getting info" % (ord(cmd))
            return
        (disk, stat) = unpack(">BB", info)
        if self.debug:
            print "cmd=%0x cmdStat disk=%d stat=%s" % (
                ord(cmd), disk, hex(stat))

    def cmdRead(self, cmd, flags=''):
        disk = -1
        lsn = -1
        rc = E_OK
        info = self.conn.read(INFOSIZ, self.timeout)
        if not info:
            print "cmd=%0x cmdRead timeout getting info" % (ord(cmd))
            return
            # rc = E_READ
            # rc = E_CRC # force a re-read
        # if rc == E_OK:
        (disk, lsn) = unpack(">BI", info[0] + NULL + info[1:])
        if self.debug:
            print "cmd=%0x cmdRead disk=%d lsn=%d" % (ord(cmd), disk, lsn)
        data = NULL_SECTOR
        if rc == E_OK:
            if self.files[disk] is None:
                rc = E_NOTRDY
        # XXX: Not needed if set on open and updated on write
        # if rc == E_OK and lsn == 0:
        #        self.files[disk].guessMaxLsn()
        if rc == E_OK and lsn >= self.files[disk].maxLsn and not self.hdbdos:
            rc = E_EOF
        if rc == E_OK:
            try:
                if self._isNamedObjDrive(disk):
                    flags += 'O'
                if not self._isNamedObjDrive(disk) and self.hdbdos:
                    disk = lsn / 630
                    lsn = lsn - (disk * 630)
                else:
                    lsn += self.files[disk].offset
                self.files[disk].seek(lsn * SECSIZ)
                assert(self.files[disk].tell() == (lsn * SECSIZ))
            except BaseException:
                raise
                rc = E_SEEK
                data = NULL_SECTOR
                print "   rc=%d" % rc
        if rc == E_OK:
            try:
                data = self.files[disk].file.read(SECSIZ)
                if len(data) == 0:
                    data = NULL_SECTOR
                    flags += 'E'
            except BaseException:
                rc = E_READ
        # Pad to SECSIZ
        if len(data) < SECSIZ:
            data=data.ljust(SECSIZ, '\x00')
            flags += "P"
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
        flags = ''
        info = self.conn.read(INFOSIZ, self.timeout)
        if not info:
            print "cmd=%0x cmdReadEx timeout getting info" % (ord(cmd))
            return
            # rc = E_READ
            # rc = E_CRC # force a re-read
        if rc == E_OK:
            (disk, lsn) = unpack(">BI", info[0] + NULL + info[1:])
        data = NULL_SECTOR
        if self.files[disk] is None:
            rc = E_NOTRDY
            # print "   rc=%d" % rc
        # XXX: not needed if it's set on open and updated on write
        # if rc == E_OK and lsn == 0:
        #        self.files[disk].guessMaxLsn()
        if rc == E_OK and lsn >= self.files[disk].maxLsn and not self.hdbdos:
            rc = E_EOF
        if rc == E_OK:
            try:
                if self._isNamedObjDrive(disk):
                    flags += 'O'
                if not self._isNamedObjDrive(disk) and self.hdbdos:
                    disk = lsn / 630
                    lsn = lsn - (disk * 630)
                    flags += "H"
                else:
                    lsn += self.files[disk].offset
                if self.files[disk].dosplus:
                    flags +="D"
                    lsn -= 1
                self.files[disk].seek(lsn * SECSIZ)
                assert(self.files[disk].tell() == (lsn * SECSIZ))
            except BaseException:
                rc = E_SEEK
                # print "   rc=%d" % rc
                traceback.print_exc()
        if rc == E_OK:
            try:
                data = self.files[disk].file.read(SECSIZ)
                # if data:
                # 	pass
                # print "cmdReadEx read %d" % len(data)
                if len(data) == 0:
                    # Seek past EOF, just return 0'ed data
                    data = NULL_SECTOR
                    flags += 'E'
                    # print "cmdReadEx eof read %d" % len(data)

            except BaseException:
                rc = E_READ
                data = NULL_SECTOR
                # print "   rc=%d" % rc
                traceback.print_exc()
        # print "cmdReadEx sending %d" % len(data)
        # Pad to SECSIZ
        if len(data) < SECSIZ:
            data=data.ljust(SECSIZ, '\x00')
            flags += "P"
        dataCrc = dwCrc16(data)
        self.conn.write(data)
        crc = self.conn.read(CRCSIZ, self.timeout)
        if not crc:
            print "cmd=%0x cmdReadEx timeout getting crc" % (ord(cmd))
            # return
            rc = E_CRC
        # print "   len(info)=%d" % len(info)
        # (crc,) = unpack(">H", info)

        if rc == E_OK:
            if crc != dataCrc:
                print "CRC: read", hex(
                    unpack(
                        ">H", crc)[0]), "expected", hex(
                    unpack(
                        ">H", dataCrc)[0])
                rc = E_CRC
            self.conn.write(chr(rc))
        elif rc != E_CRC:
            self.conn.write(chr(rc))
        if self.debug or rc != E_OK:
            print "cmd=%0x cmdReadEx disk=%d lsn=%d rc=%d f=%s" % (
                ord(cmd), disk, lsn, rc, flags)
        # print "   rc=%d" % rc

    def cmdReReadEx(self, cmd):
        self.cmdReadEx(cmd, 'R')

    def cmdWrite(self, cmd, flags=''):
        # print "cmd=%0x cmdWrite" % ord(cmd)
        rc = E_OK
        disk = -1
        lsn = -1
        data = ''
        info = self.conn.read(INFOSIZ, self.timeout)
        if not info:
            print "cmd=%0x cmdWrite timeout getting info" % (ord(cmd))
            return
            # rc = E_WRITE
            # rc = E_CRC # force a re-write
        if rc == E_OK:
            data = self.conn.read(SECSIZ, self.timeout)
        if not data:
            print "cmd=%0x cmdWrite timeout getting data" % (ord(cmd))
            # return
            # rc = E_WRITE
            rc = E_CRC  # force a re-write
        if rc == E_OK:
            crc = self.conn.read(CRCSIZ, self.timeout)
            if not crc:
                print "cmd=%0x cmdWrite timeout getting crc" % (ord(cmd))
                # return
                rc = E_CRC  # force a re-write
            else:
                (disk, lsn) = unpack(">BI", info[0] + NULL + info[1:])
                if crc != dwCrc16(data):
                    rc = E_CRC
        if rc == E_OK and self.files[disk] is None:
            rc = E_NOTRDY
        if rc == E_OK:
            # Note: Write is allowed for non-os9 images
            if self.files[disk].os9Image and lsn >= self.files[disk].maxLsn:
                rc = E_EOF
        if rc == E_OK:
            try:
                if self._isNamedObjDrive(disk):
                    flags += 'O'
                if not self._isNamedObjDrive(disk) and self.hdbdos:
                    disk = lsn / 630
                    lsn = lsn - (disk * 630)
                    flags += "H"
                else:
                    lsn += self.files[disk].offset
                if self.files[disk].dosplus:
                    flags +="D"
                    lsn -= 1
                self.files[disk].seek(lsn * SECSIZ)
            except BaseException:
                traceback.print_exc()
                rc = E_SEEK

        if rc == E_OK:
            try:
                self.files[disk].file.write(data)
                self.files[disk].file.flush()
            except Exception as e:
                rc = E_WRITE
                if e.message == 'File not open for writing':
                    rc = E_WRPROT
                print traceback.print_exc()
        if rc == E_OK and not self._isNamedObjDrive(disk):
            if (lsn == 0) or (
                    not self.files[disk].os9Image and lsn >= self.files[disk].maxLsn):
                self.files[disk].guessMaxLsn()
        # if crc != dwCrc16(data):
        # 	rc=E_CRC
        self.conn.write(chr(rc))
        if self.debug or rc != E_OK:
            print "cmd=%0x cmdWrite disk=%d lsn=%d rc=%d f=%s" % (
                ord(cmd), disk, lsn, rc, flags)
        # print "   rc=%d" % rc

    def cmdReWrite(self, cmd):
        self.cmdWrite(cmd, 'R')

    # XXX Java version will return oldest data first
    def cmdSerRead(self, cmd):
        data = NULL * 2
        msg = "NoData"
        # msg = ""
        for channel in self.channels:
            nchannel = ord(channel)
            ow = self.channels[channel].outWaiting()
            if ow < 0:
                # Channel is closing
                data = chr(16)
                data += channel
                msg = "channel=%d Closing" % nchannel
                if self.channels[channel].state == DWV_S_CLOSED:
                    self.channels[channel].close()
                    del self.channels[channel]
                break
            elif ow == 0:
                continue
            elif ow < 3:
                data = chr(1 + nchannel)
                data += self.channels[channel].read(1)
                msg = "channel=%d ByteWaiting=(%s)" % (nchannel, data[1])
                break
            else:
                data = chr(17 + nchannel)
                data += chr(ow)
                msg = "channel=%d BytesWaiting=%d" % (nchannel, ow)
                break
        # elif ow<0:
        # 	# Channel is closing
        # 	data = chr(16)
        # 	data += chr(1)

        self.conn.write(data)
        if self.debug and msg:
            print "cmd=%0x serRead %s" % (ord(cmd), msg)

    # XXX
    def cmdReset(self, cmd):
        if self.debug:
            print "cmd=%0x cmdReset" % ord(cmd)

    # XXX
    def cmdInit(self, cmd):
        for drive in range(len(self.files)):
            if not self.files[drive]:
                continue
            self.reset(drive)
        for channel in self.channels:
            self.channels[channel].close()
            if self.debug:
                print(
                    "cmd=%0x cmdInit channel=%d closed" %
                    (ord(cmd), ord(channel)))
        for channel in self.channels.keys():
            del self.channels[channel]
        if self.debug:
            print "cmd=%0x cmdInit" % ord(cmd)

    def cmdNop(self, cmd):
        if self.debug:
            print "cmd=%0x cmdNop" % ord(cmd)

    # XXX
    def cmdTerm(self, cmd):
        if self.debug:
            print "cmd=%0x cmdTerm" % ord(cmd)

    # enhanced DwInit with combo lock
    # Combo lock stage 1: send 'p' OP_DWINIT must return 'p'
    # Combo lock stage 2: send 'y' OP_DWINIT must return 'y'
    # Combo lock stage 3: send request for information page
    #   Server Enabled Features Page 1: 'E'
    #       Bit definitions - see FEATURE defs in dwconstants.py
    #       combo lock disabled
    #   Server Available Features Page 1: 'F'
    #       Bit definitions - see FEATURE defs in dwconstants.py
    #       combo lock disabled
    #    Server Version Page 1: 'V'
    #       bits 4-7 major binary 0-15
    #       bits 0-3 minor msb bcd 0-9
    #       combo lock disabled
    #    Server Version Page 2: 'v'
    #       bits 4-7 minor lsb bcd 0-9
    #       bits 0-3 sub - 0=none, 1='a', 2='b' etc.
    #       combo lock disabled
    def cmdDWInit(self, cmd):
        r = 0xff
        clientID = self.conn.read(1, self.timeout)
        if not clientID:
            clientID = '\xff'
        if self.debug:
            print("Combo Lock: %0x" % self.comboLock)
            print("Client Id: %0x(%s)" % (ord(clientID),clientID=='p'))
        if self.comboLock == 0:
            if clientID == 'p':
                r = ord(clientID)
                self.comboLock = 1
            else:
                self.comboLock = 0
        elif self.comboLock == 1:
            if clientID == 'y':
                r = ord(clientID)
                self.comboLock = 2
            else:
                self.comboLock = 0
        elif self.comboLock == 2:
            r = 0
            if clientID == 'E':
                r |= FEATURE_EMCEE
                r |= FEATURE_DLOAD if self.dload else 0
                r |= FEATURE_HDBDOS if self.hdbdos else 0
                r |= FEATURE_DOSPLUS if self.dosplus else 0
                if 'printer' in self.args.experimental:
                    r |= FEATURE_PRINTER
                if 'ssh' in self.args.experimental:
                    r |= FEATURE_SSH
                if 'playsound' in self.args.experimental:
                    r |= FEATURE_PLAYSND
                self.comboLock = 0
            if clientID == 'F':
                r |= FEATURE_EMCEE
                r |= FEATURE_DLOAD
                r |= FEATURE_HDBDOS
                r |= FEATURE_DOSPLUS
                r |= FEATURE_PRINTER
                r |= FEATURE_SSH
                r |= FEATURE_PLAYSND
                self.comboLock = 0
            elif clientID == 'V':
                    r |= (PYDW_VERSION_MAJOR << 4) & 0xf0
                    minorMsb = (PYDW_VERSION_MINOR//10) & 0x0f
                    r |= minorMsb
                    self.comboLock = 0
            elif clientID == 'v':
                    minorLsb = (PYDW_VERSION_MINOR%10)
                    r |= (minorLsb << 4) & 0xf0
                    code = (ord(PYDW_VERSION_SUB)-ord('a')+1) if PYDW_VERSION_SUB else 0
                    r |= code & 0x0f
                    self.comboLock = 0
            else:
                self.comboLock = 0
        else:
            self.comboLock = 0
        if self.debug:
            print "cmd=%0x cmdDWInit cl=%0x id=%0x r=%0x" % (ord(cmd), self.comboLock, ord(clientID), r)
        self.conn.write(chr(r))

    def cmdTime(self, cmd):
        t = ''
        now = time.localtime()
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
        # if channel not in self.channels:
        # 	print("cmd=%0x cmdSerSetStat bad channel=%d" % (ord(cmd),ord(channel)))
        # 	return
        code = self.conn.read(1, self.timeout)
        if not code:
            print(
                "cmd=%0x cmdSerSetStat channel=%d timeout getting code" %
                (ord(cmd), ord(channel)))
            return
        data = ''
        if code == SS_Open:
            self.channels[channel] = DWVModem(self, channel, debug=self.debug)
            if self.debug:
                print("cmd=%0x SS_Open channel=%d" % (ord(cmd), ord(channel)))
        if code == SS_ComSt:
            data = self.conn.read(26, self.timeout)
        if channel not in self.channels:
            print(
                "cmd=%0x cmdSerSetStat bad channel=%d code=%0x" %
                (ord(cmd), ord(channel), ord(code)))
        # 	return
        elif code == SS_Close:
            self.channels[channel].close()
            del self.channels[channel]
            if self.debug:
                print("cmd=%0x SS_Close channel=%d" % (ord(cmd), ord(channel)))
        if self.debug:
            print("cmd=%0x cmdSerSetStat channel=%d code=%0x len=%d" %
                  (ord(cmd), ord(channel), ord(code), len(data)))

    def cmdSerGetStat(self, cmd):
        channel = self.conn.read(1, self.timeout)
        if not channel:
            print("cmd=%0x cmdSerGetStat timeout getting channel" % (ord(cmd)))
            return
        if channel not in self.channels:
            print(
                "cmd=%0x cmdSerGetStat bad channel=%d" %
                (ord(cmd), ord(channel)))
            return
        code = self.conn.read(1, self.timeout)
        if not code:
            print(
                "cmd=%0x cmdSerGetStat channel=%d timeout getting code" %
                (ord(cmd), ord(channel)))
            return
        if self.debug:
            print(
                "cmd=%0x cmdSerGetStat channel=%d code=%0x" %
                (ord(cmd), ord(channel), ord(code)))

    def cmdSerInit(self, cmd):
        channel = self.conn.read(1, self.timeout)
        if not channel:
            print("cmd=%0x cmdSerInit timeout getting channel" % (ord(cmd)))
            return
        if channel in self.channels:
            print(
                "cmd=%0x cmdSerInit existing channel=%d" %
                (ord(cmd), ord(channel)))
            return
        self.channels[channel] = DWVModem(self, channel, debug=self.debug)
        if self.debug:
            print("cmd=%0x cmdSerInit channel=%d" % (ord(cmd), ord(channel)))

    def cmdSerTerm(self, cmd):
        channel = self.conn.read(1, self.timeout)
        if not channel:
            print("cmd=%0x cmdSerTerm timout getting channel" % (ord(cmd)))
            return
        if channel not in self.channels:
            print(
                "cmd=%0x cmdSerTerm bad channel=%d" %
                (ord(cmd), ord(channel)))
            return
        self.channels[channel].close()
        del self.channels[channel]
        if self.debug:
            print("cmd=%0x cmdSerTerm channel=%d" % (ord(cmd), ord(channel)))

    def cmdFastWrite(self, cmd):
        channel = chr(ord(cmd) - 0x80)
        if channel not in self.channels:
            print(
                "cmd=%0x cmdFastWrite bad channel=%d" %
                (ord(cmd), ord(channel)))
            return
        byte = self.conn.read(1, self.timeout)
        if not byte:
            print(
                "cmd=%0x cmdFastWrite channel=%d timeout" %
                (ord(cmd), ord(channel)))
            return
        self.channels[channel].write(byte)
        self.channels[channel]._cmdWorker()
        if self.debug:
            print(
                "cmd=%0x cmdFastWrite channel=%d byte=%0x" %
                (ord(cmd), ord(channel), ord(byte)))

    def cmdSerReadM(self, cmd):
        channel = self.conn.read(1, self.timeout)
        if not channel:
            print("cmd=%0x cmdSerReadM timout getting channel" % (ord(cmd)))
            return
        if channel not in self.channels:
            print(
                "cmd=%0x cmdSerReadM bad channel=%d" %
                (ord(cmd), ord(channel)))
            return
        num = self.conn.read(1, self.timeout)
        if not num:
            print(
                "cmd=%0x cmdSerReadM channel=%d timeout getting count" %
                (ord(cmd), ord(channel)))
            return
        data = self.channels[channel].read(ord(num))
        self.conn.write(data)
        if self.debug:
            print(
                "cmd=%0x cmdSerReadM channel=%d num=%d" %
                (ord(cmd), ord(channel), ord(num)))

    def cmdSerWriteM(self, cmd):
        channel = self.conn.read(1, self.timeout)
        if not channel:
            print("cmd=%0x cmdSerWriteM timout getting channel" % (ord(cmd)))
            return
        if channel not in self.channels:
            print(
                "cmd=%0x cmdSerWriteM bad channel=%d" %
                (ord(cmd), ord(channel)))
            return
        num = self.conn.read(1, self.timeout)
        if not num:
            print(
                "cmd=%0x cmdSerWriteM channel=%d timeout getting count" %
                (ord(cmd), ord(channel)))
            return
        data = self.conn.read(ord(num), self.timeout)
        self.channels[channel].write(data)
        if self.debug:
            print(
                "cmd=%0x cmdSerWriteM channel=%d num=%d" %
                (ord(cmd), ord(channel), ord(num)))
        self.channels[channel]._cmdWorker()

    def cmdSerWrite(self, cmd):
        channel = self.conn.read(1, self.timeout)
        if not channel:
            print("cmd=%0x cmdSerWrite timout getting channel" % (ord(cmd)))
            return
        if channel not in self.channels:
            print(
                "cmd=%0x cmdSerWrite bad channel=%d" %
                (ord(cmd), ord(channel)))
            return
        byte = self.conn.read(1, self.timeout)
        if not byte:
            print(
                "cmd=%0x cmdSerWrite channel=%d timeout getting byte" %
                (ord(cmd), ord(channel)))
            return
        self.channels[channel].write(byte)
        if self.debug:
            print(
                "cmd=%0x cmdSerWrite channel=%d byte=%0x" %
                (ord(cmd), ord(channel), ord(byte)))
        self.channels[channel]._cmdWorker()

    def cmdPrint(self, cmd):
        data = self.conn.read(1, self.timeout)
        if self.vprinter:
            self.vprinter.write(data)
        else:
            print(
                "cmd=%0x cmdPrint byte=%0x WARN: printing not enabled" %
                (ord(cmd), ord(data)))
        if self.debug:
            print("cmd=%0x cmdPrint byte=%0x" % (ord(cmd), ord(data)))

    def cmdPrintFlush(self, cmd):
        if self.vprinter:
            self.vprinter.printFlush()
        else:
            print(
                "cmd=%0x cmdPrintFlush WARN: printing not enabled" %
                (ord(cmd)))
        if self.debug:
            print("cmd=%0x cmdPrintFlush" % (ord(cmd)))

    def _NamedObjCore(self, mode):
        drive = 255
        fn = None
        data = self.conn.read(1, self.timeout)
        if not data:
            drive = 0
        if drive:
            nameLen = ord(data)
            fn = self.conn.read(nameLen, self.timeout)
            if not fn:
                drive = 0
        if drive:
            fn2 = self.aliases['namedobj'].get(fn.upper(), None)
            if fn2 != None:
                print('Alias: %s -> %s' % (fn, fn2))
                fn = fn2
            pwd = os.getcwd()
            os.chdir(self.dirs['namedobj'])
            exists = os.path.exists(fn)
            if mode.startswith('r'):
                if not exists:
                    drive = 0
                else:
                    if (self.files[drive] is None) or (self.files[drive] and self.files[drive].file.name != fn):
                        self.open(drive, fn, mode='ab+', raw=True, proto='namedobj', dosplus=False)
                        self.namedObjDrive = drive

            if mode.startswith('w'):
                if exists:
                    drive = 0
                else:
                    self.open(drive, fn, mode='ab+', raw=True, proto='namedobj', dosplus=False)
                    self.namedObjDrive = drive
            os.chdir(pwd)
        self.conn.write(chr(drive))
        return drive, fn

    def cmdNamedObjMount(self, cmd):
        drive, fn = self._NamedObjCore('r')
        if drive == 0:
            print("cmd=%0x cmdNamedObjMount: Error: %s" % (ord(cmd), fn))
        if self.debug:
            print("cmd=%0x cmdNamedObjMount drive=%d" % (ord(cmd), drive))

    def cmdNamedObjCreate(self, cmd):
        drive, fn = self._NamedObjCore('w')
        if drive == 0:
            print("cmd=%0x cmdNamedObjCreate: Error: %s" % (ord(cmd), fn))
        if self.debug:
            print("cmd=%0x cmdNamedObjCreate drive=%d" % (ord(cmd), drive))

    # $FA - PlaySound Extension
    # Plays a sound out of the default system audio device
    #
    # Prerequisites: Must enable experimental feature flag:
    #     -x playsound
    #     option experimental playsound
    # 
    # Byte Value Description
    # ---- ----- ------------
    #    1  $FA  OP_PLAYSOUND
    #    2    N  Length
    #  3+N    -  Filename
    #    
    # Return Value:
    #    0 - OK
    #  $F4 - ERROR - File not found
    #  $FA - ERROR - Playsound Not enabled
    #
    def _doPlaySound(self, name):
        err = E_OK
        if 'playsound' in self.args.experimental:
            import playsound
            from playsound import playsound
        else:
            err = E_PLAYSOUND
            print("Playsound not enabled. use: -x playsound")
        if not err:
            fn2 = self.aliases['playsound'].get(name.upper(), None)
            if fn2 != None:
                print('Alias: %s -> %s' % (name, fn2))
                name = fn2
            pwd = os.getcwd()
            os.chdir(self.dirs['playsound'])
            try:
                if not os.path.exists(name):
                    err = E_READ
            except TypeError:
                err = E_READ
            os.chdir(pwd)

        if not err:
            direct = False
            #if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            #    machine = platform.machine()
            #    if machine.startswith('arm') or machine.startswith('aarch'):
            #        direct = True
            if direct:
               _playsound(name, False)
            else:
               proc = multiprocessing.Process(target=_playsound, args=(name, self.dirs['playsound'], True))
               self.procs.append(proc)
               proc.start()
        return err

    def cmdPlaySound(self, cmd):
        err = E_OK
        if 'playsound' not in self.args.experimental:
            err = E_PLAYSOUND
            print("Playsound not enabled. use: -x playsound")
        data = self.conn.read(1, self.timeout)
        length = unpack(">B", data)[0]
        name = None
        if length > 0:
            name = self.conn.read(length, self.timeout)
        else:
            err = E_READ

        if not err:
            err = self._doPlaySound(name)
        self.conn.write(chr(err))
        if self.debug or err:
            print("cmd=%0x rc=%d playsound(%s)" % (ord(cmd), err, name))

    def cmdPlaySoundStop(self, cmd):
        count = len(self.procs)
        for proc in self.procs:
            proc.terminate()
        self.procs = []
        if self.debug:
            print("cmd=%0x playsound stop: %d procs" % (ord(cmd), count))

    def cmdErr(self, cmd):
        print("cmd=%0x cmdErr" % ord(cmd))
        # raise Exception("cmd=%0x cmdErr" % ord(cmd))

    # ## EmCee Server # ##
    def _emCeeLoadFile(self, filnum, fname, fmode, ftyp=0, opn=False, error=0):
        address = 0
        size = 0
        checksum = 0
        if not error:
            try:
                fname = self.aliases['mc'].get(fname.upper(), fname)
                os.chdir(self.dirs['mc'])
                if os.path.exists(fname):
                   self.files[filnum] = CocoCas(fname, fmode)
                   self.files[filnum].seek()
                   # self.files[filnum] = MlFileReader(fname, fmode, ftyp)
                   # if ftyp == 2: # ml file
                   #        self.files[filnum].readHeader()
                   #        address = self.files[filnum].addr
                   #        size = self.files[filnum]# .
                else:
                   error = E_MC_NE
            except IOError as e:
                if e.errno == 21:
                    error = E_MC_FN
                elif e.errno == 13:
                    error = E_MC_FM
                else:
                    error = E_MC_FS
            except BaseException as e:
                error = E_MC_IO
        if not error:
            try:
                data = self.files[filnum].read(temp=True)
                stat = self.files[filnum].stat()
                size = stat['blk']['blklen']
                address = stat['nf']['current']
                # length = min(SECSIZ, self.files[filnum].length)
                # data = self.files[filnum].tempRead(length)
                if data:
                    checksum = unpack(">H", dwCrc16(data))[0]
                else:
                    error = E_MC_IO
            except BaseException:
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
            name = self.aliases['mc'].get(name.upper(), name)
            self.files[filnum] = CocoCas(name, 'wb')
            load = start = ascflg = 0
            ascflg = 0xff
            if mode == 2:
                load = size
                start = exaddr
                filetype = 2  # ml
                ascflg = 0
            elif mode == 0:
                filetype = 0  # basic
                ascflg = 0  # basic
            else:
                filetype = 1  # data
            os.chdir(self.dirs['mc'])
            nf = CocoCasNameFile(
                filename=name.split(os.path.sep)[-1].split('.')[0][:8].upper(),
                filetype=filetype,
                ascflg=ascflg,
                gap=1,
                load=load,
                start=start,
            )
            nfblk = CocoCasBlock(nf.getBlockData(), blktyp=0)  # namefile
            self.files[filnum].nf = nf
            self.files[filnum].writeBlock(nfblk)
        self.conn.write(chr(error))
        return error

    def cmdEmCeeLoadFile(self, cmd):
        error = 0
        info = self.conn.read(2, self.timeout)
        if not info:
            print(
                "cmd=%0x cmdEmCeeLoadFile timout getting command info" %
                (ord(cmd)))
            error = E_MC_IO  # IO ERROR
        if not error:
            ftyp = ord(info[0])
            fnamelen = ord(info[1])
            fname = self.conn.read(fnamelen, self.timeout)
            if not fname:
                print(
                    "cmd=%0x cmdEmCeeLoadFile timout getting file name" %
                    (ord(cmd)))
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
            print(
                "cmd=%0x cmdEmCeeLoadFile timout getting command info" %
                (ord(cmd)))
            error = E_MC_IO  # IO ERROR
        if not error:
            finfo = ord(info[0])
            filnum = finfo & 0x0f
            fmode = fmodes[((finfo & 0xc0) >> 6)]
            fnamelen = ord(info[1])
            fname = self.conn.read(fnamelen, self.timeout)
            if not fname:
                print(
                    "cmd=%0x cmdEmCeeLoadFile timout getting file name" %
                    (ord(cmd)))
                error = E_MC_FN
        if fmode.startswith('r'):
            error = self._emCeeLoadFile(
                filnum, fname, fmode, opn=True, error=error)
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
                if fh is None:
                    error = E_MC_NO
            except BaseException:
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
                    # length = min(SECSIZ, self.files[filnum].length)
                    # data = self.files[filnum].tempRead(length)
                    if data:
                        checksum = unpack(">H", dwCrc16(data))[0]
                    else:
                        error = E_MC_IO + 100
            except BaseException:
                raise
                error = E_MC_IO + 200

        # if not error:
        #    length = min(SECSIZ, fh.remaining)
        #    if length == 0 and fh.ftyp == 2 and fh.typ != 0xff: # Last block and
        #                fh.readHeader()
        #    try:
        #        # data = fh.tempRead(length)
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
                self.files[fileNum].writeBlock(
                    CocoCasBlock("\xff\x00\xff\x55"))
                self.files[fileNum].close()
            else:
                data = self.conn.read(size, self.timeout)
                if not data:
                    error = E_MC_IO
                if not error:
                    i = 0
                    while i < len(data):
                        j = i + 255
                        self.files[fileNum].writeBlock(
                            CocoCasBlock(data[i:j], blktyp=1))
                        i = j
        # if not error:
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
        self.conn.write(chr(error) + chr(length))

    def cmdEmCeeDirFile(self, cmd):
        error = 0
        flag = 0
        dirNam = os.getcwd()
        try:
            flag = ord(self.conn.read(1, self.timeout))
            length = ord(self.conn.read(1, self.timeout))
        except BaseException:
            error = E_MC_IO
        if self.debug:
            print(
                "cmd=%0x cmdEmCeeDirFile flag=%d length=%d" %
                (ord(cmd), flag, length))
        if not error and length > 0:
            try:
                dirNam = self.conn.read(length, self.timeout)
            except BaseException:
                error = E_MC_IO
        if not error:
            if flag == 0:
                try:
                    dirNam = self.aliases['mc'].get(dirNam.upper(), dirNam)
                    os.chdir(self.dirs['mc'])
                    self.emCeeDir = os.listdir(dirNam)
                    self.emCeeDirIdx = 0
                except BaseException:
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
        except BaseException:
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
        except BaseException:
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
        except BaseException:
            error = E_MC_IO
        if not error:
            try:
                dirNam = self.conn.read(length, self.timeout)
            except BaseException:
                raise
                error = E_MC_IO
        if not error:
            try:
                dirNam = self.aliases['mc'].get(dirNam.upper(), dirNam)
                self.dirs['mc'] = dirNam
            except BaseException:
                error = E_MC_NE
        self.conn.write(chr(error))
        if self.debug:
            print("cmd=%0x cmdEmCeeSetDir" % ord(cmd))

    def cmdEmCeePrint(self, cmd):
        data = self.conn.read(1, self.timeout)
        if self.vprinter:
            self.vprinter.write(data)
        if self.debug:
            print("cmd=%0x cmdEmCeePrint byte=%0x" % (ord(cmd), ord(data)))

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
        MC_PRINT: cmdEmCeePrint,
    }

    def doEmCeeCmd(self, cmd):
        mccmd = self.conn.read(1)
        if mccmd:
            try:
                f = DWServer.mccommand[mccmd]
            except BaseException:
                f = lambda s, x: DWServer.cmdEmCeeErr(s, x)
            f(self, mccmd)

    # DLOAD Commands
    def _dloadFindFile(self, fn):
        ftype = DLOAD_FT_FNF
        aflag = DLOAD_AF_ASCII 
        pwd = os.getcwd()
        os.chdir(self.dirs['dload'])
        if os.path.exists(fn):
            with open(fn) as f:
                fb = f.read(1)
                if fb == '\x00':
                    ftype = DLOAD_FT_ML
                    aflag = DLOAD_AF_BIN
                else:
                    ftype = DLOAD_FT_BASIC
                    aflag = DLOAD_AF_ASCII

        os.chdir(pwd)
        return(ftype, aflag)

    # DLOAD Open File
    def dloadFileReq(self, cmd):
        # 2.  Host to BASIC - P.FILR
        self.conn.write(DLOAD_P_FILR)

        # 3.  BASIC to host - 
        #    1.  8 byte filename, left justified, blank filled
        #    2.  XOR of the bytes in the filename
        data = self.conn.read(9)
        fn = data[:8]
        xb = data[8]

        # Check XOR byte
        #     4.  Host to BASIC -
        #         a) If no errors detected -
        #         1.  P.ACK
        #         b) If errors detected, P.NAK.
        if xb == dloadXor(fn):
            rc = DLOAD_P_ACK
        else:
            rc = DLOAD_P_NAK
        self.conn.write(rc)


        #     4.  Host to BASIC -
        #         a) If no errors detected -
        if rc == DLOAD_P_ACK:
            #         2.  file type (0=BASIC program, 2=machine language,
            #             FF=file not found)
            #         3.  ASCII flag (0=binary file, FF=ASCII)
            fn = fn.strip()
            fn2 = self.aliases['dload'].get(fn.upper(), fn)
            wd = os.getcwd()
            if fn2 != fn:
                print('Alias: %s -> %s' % (fn, fn2))
                fn = fn2
            else:
                os.chdir(self.dirs['dload'])
            (ftype, aflag) = self._dloadFindFile(fn)
            data = pack('>ss', ftype, aflag)

            # 4.  XOR of file type and ASCII flag.
            xb = dloadXor(data)

            data = pack('>2ss', data, xb)
            self.conn.write(data)

            if ftype != DLOAD_FT_FNF:
                if aflag == DLOAD_AF_ASCII:
                    eolxlate = self.args.dloadTranslate
                else:
                    eolxlate = False
                pwd = os.getcwd()
                os.chdir(self.dirs['dload'])
                self.open(0, fn, mode='r', offset=0, hdbdos=False, raw=True,
                          eolxlate=eolxlate, proto='dload', dosplus=False)
                os.chdir(pwd)
                self.files[0].ftype = ftype
                self.files[0].ftype = aflag
            os.chdir(wd) 

        if self.debug:
            msg = "dloadFileReq: rc=%x" % (ord(rc))
            if rc == DLOAD_P_ACK:
                msg = "%s fn=%s ftype=%x ascii=%x" % (msg, fn, ord(ftype), ord(aflag))
            print(msg)

    def dloadBlockReq(self, cmd):
        # 2.  Host to BASIC - P.BLKR
        self.conn.write(DLOAD_P_BLKR)

        # 3.  BASIC to host -
        #    1.  Block number (most significant 7 bits)
        #    2.  Block number (least significant 7 bits)
        #    3.  XOR of block number bytes
        data = self.conn.read(3)
        (blkmsb, blklsb, xb) = unpack('>BBc', data)

        # 4.  Host to BASIC -
        #    a) If no errors detected -
        #        1.  P.ACK
        #    b) If errors detected, P.NAK.
        # Check XOR BYTE
        rc = DLOAD_P_ACK
        xb2 = dloadXor(data[:2])
        if dloadXor(data[:2]) != xb:
            print(1, ord(xb), ord(xb2))
            rc = DLOAD_P_NAK

        # Check legal block requested
        eof = False
        if rc == DLOAD_P_ACK:
            # combine MSB and LSB into single 14-bit block number
            blk = (blkmsb << DLOAD_MSB_SHIFT) | blklsb
            # File offset
            offset = blk * DLOAD_BLOCK_SIZE
            img_size = self.files[0].img_size
            if offset > img_size:
                eof = True
                #print(2)
                #rc = DLOAD_P_NAK

        # write status
        self.conn.write(rc)

        # Continue
        # 4.  Host to BASIC -
        #    a) If no errors detected -
        #        2.  Block  length  in  bytes  (0  through  128,   0
        #            indicating end of file)
        #        3.  128 bytes of data
        #        4.  XOR of block length and data bytes

        # NOTE: 128  bytes  of  data  must   be   sent,
        # regardless of the block length.  If the
        # block length is less than 128 the extra
        # bytes  are  read by BASIC but not used,
        # so their values are of no concern.
        if rc == DLOAD_P_ACK:
            if eof:
                # eof - empty data
                fdata = ''
            else:
                self.files[0].file.seek(offset)
                fdata = self.files[0].file.read(DLOAD_BLOCK_SIZE)
            # data length
            dl = len(fdata)
            # pad data to 128 bytes
            if dl < DLOAD_BLOCK_SIZE:
                fdata = fdata.ljust(DLOAD_BLOCK_SIZE, '\x00')
            data = '%s%s'% (chr(dl), fdata)
            # Calculate XOR check byte
            xb = dloadXor(data)
            data = '%s%s'% (data, xb)
            self.conn.write(data)

        if self.debug:
            msg = "dloadBlockReq: rc=%x" % (ord(rc))
            if rc == DLOAD_P_ACK:
                msg = "%s blk=%d len=%d" % (msg, blk, dl)
                if eof:
                    msg = '%s EOF' % (msg)
            print(msg)

    def dloadErr(self, cmd):
        rc = DLOAD_P_NAK
        self.conn.write(rc)
        if self.debug:
            print("dloadErr: rc=%x" % (ord(rc)))

    # DLOAD Command jump table
    dloadcommand = {
            DLOAD_P_FILR: dloadFileReq,
            DLOAD_P_BLKR: dloadBlockReq,
    }


    # DriveWire Command jump table
    dwcommand = {
        OP_NOP: cmdNop,
        OP_NAMEOBJ_MOUNT: cmdNamedObjMount,
        OP_NAMEOBJ_CREATE: cmdNamedObjCreate,
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
        OP_PLAYSOUND: cmdPlaySound,
        OP_PLYSNDSTP: cmdPlaySoundStop,
    }

    def main(self):
        while True:
            for proc,alive in [(proc, proc.is_alive()) for proc in self.procs]:
               if not alive:
                  proc.terminate()
                  self.procs.remove(proc)

            cmd = self.conn.read(1)
            if cmd:
                if self.dload:
                    try:
                        f = DWServer.dloadcommand[cmd]
                    except KeyError:
                        f = lambda s, x: DWServer.dloadErr(s, x)
                else:
                    try:
                        f = DWServer.dwcommand[cmd]
                    except KeyError:
                        f = lambda s, x: DWServer.cmdErr(s, x)
                f(self, cmd)


class TestConn:
    def __init__(self):
        self.i = 0

    def read(self, n):
        cmd = DWServer.dwcommand.keys()[self.i]
        self.i = (self.i + 1) % len(DWServer.dwcommand.keys())
        return cmd

    def write(self, buf):
        for c in buf:
            d = c if (ord(c) >= 32 and ord(c) < 128) else '.'
            print "%s(%s) " % (hex(ord(c)), d),
        print


if __name__ == '__main__':
    testConn = TestConn()
    server = DWServer(testConn)
    server.main()


# XXX: cleanup required
# vim: ts=4 sw=4 sts=4 expandtab
