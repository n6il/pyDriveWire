import threading
import traceback
import subprocess
from dwsocket import *
from dwtelnet import DWTelnet
import os
import sys
import re
import urlparse
import tempfile
from dwserial import DWSerial


class ParseNode:
    def __init__(self, name, nodes=None):
        self.name = name
        self.nodes = {}
        if nodes:
            self.nodes = nodes

    def add(self, key, val):
        self.nodes[key] = val

    def lookup(self, key):
        if not key:
            return None
        # exact match
        r = self.nodes.get(key, None)
        if r:
            return r
        key = key.lower()
        r = self.nodes.get(key, None)
        if r:
            return r
        # search partial
        allNodes = self.nodes.keys()
        for i in range(len(key) + 1):
            s = key[:i]
            nodes = [n for n in allNodes if n.startswith(s)]
            # print i,"(%s"%s,nodes
            if len(nodes) == 1:
                key = nodes[0]
                return self.nodes.get(key, None)
        return None

    def repr(self):
        return str(nodes)

    def help(self):
        p = []
        if self.name:
            p.append(self.name)
        p.append("commands:")
        p.extend(self.nodes.keys())
        return "%s" % (' '.join(p))


class ATParseNode(ParseNode):
    def __init__(self, name, nodes=None):
        ParseNode.__init__(self, name, nodes)

    def lookup(self, key):
        k = key[0]
        r = ParseNode.lookup(self, k)
        if not r:
            k = key[0:1]
            r = ParseNode.lookup(self, k.upper())
        return r

    def help(self):
        # if self.name:
        # 	p.append(self.name)
        p = ["commands:"]
        p.extend(["AT%s" % k for k in self.nodes])
        return "%s" % (' '.join(p))


class ParseAction:
    def __init__(self, fn):
        self.fn = fn

    def call(self, *args):
        return self.fn(*args)

    def repr(self):
        return fn


class DWParser:
    def setupParser(self):
        diskParser = ParseNode("disk")
        diskParser.add("insert", ParseAction(self.doInsert))
        diskParser.add("reset", ParseAction(self.doReset))
        diskParser.add("eject", ParseAction(self.doEject))
        diskParser.add("show", ParseAction(self.doShow))
        diskParser.add("offset", ParseAction(self.doDiskOffset))
        diskParser.add("create", ParseAction(self.doDiskCreate))
        diskParser.add("info", ParseAction(self.doDiskInfo))
        diskParser.add("dosplus", ParseAction(self.doDiskDosPlus))

        serverParser = ParseNode("server")
        serverParser.add("instance", ParseAction(self.doInstanceShow))
        serverParser.add("dir", ParseAction(self.doDir))
        serverParser.add("list", ParseAction(self.doList))
        serverParser.add("dump", ParseAction(self.dumpstacks))
        serverParser.add("debug", ParseAction(self.doDebug))
        serverParser.add("timeout", ParseAction(self.doTimeout))
        serverParser.add("version", ParseAction(self.doVersion))
        serverParser.add("hdbdos", ParseAction(self.doHdbDos))
        serverParser.add("dosplus", ParseAction(self.doServerDosPlus))
        connParser = ParseNode("conn")
        connParser.add("debug", ParseAction(self.doConnDebug))
        serverParser.add("conn", connParser)
        serverParser.add("pwd", ParseAction(self.doPwd))
        serverParser.add("getdir", ParseAction(self.doDwGetDir))
        serverParser.add("setdir", ParseAction(self.doDwSetDir))

        portParser = ParseNode("port")
        portParser.add("show", ParseAction(self.doPortShow))
        portParser.add("close", ParseAction(self.doPortClose))
        portParser.add("debug", ParseAction(self.doPortDebug))
        portParser.add("term", ParseAction(self.doPortTerm))
        portParser.add("rows", ParseAction(self.doPortRows))
        portParser.add("cols", ParseAction(self.doPortCols))
        # portParser.add("size", ParseAction(self.doPortSize)) XXX: Not working

        instanceParser = ParseNode("instance")
        instanceParser.add("show", ParseAction(self.doInstanceShow))
        instanceParser.add("add", ParseAction(self.doInstanceShow))
        instanceParser.add("select", ParseAction(self.doInstanceSelect))

        printParser = ParseNode("printer")
        printParser.add("flush", ParseAction(self.doPrintFlush))
        printParser.add("format", ParseAction(self.doPrintFormat))
        printParser.add("file", ParseAction(self.doPrintFile))
        printParser.add("dir", ParseAction(self.doPrintDir))
        printParser.add("prefix", ParseAction(self.doPrintPrefix))
        printParser.add("cmd", ParseAction(self.doPrintCmd))
        printParser.add("status", ParseAction(self.doPrintStatus))

        configParser = ParseNode("config")
        configParser.add("show", ParseAction(self.doConfigShow))
        configParser.add("save", ParseAction(self.doConfigSave))

        dwParser = ParseNode("dw")
        dwParser.add("disk", diskParser)
        dwParser.add("server", serverParser)
        dwParser.add("port", portParser)
        dwParser.add("instance", instanceParser)
        dwParser.add("printer", printParser)
        dwParser.add("config", configParser)

        tcpParser = ParseNode("tcp")
        tcpParser.add("connect", ParseAction(self.doConnect))
        tcpParser.add("listen", ParseAction(self.doListen))
        tcpParser.add("join", ParseAction(self.doJoin))
        tcpParser.add("kill", ParseAction(self.doKill))

        atParser = ATParseNode("AT")
        atParser.add(
            "",
            ParseAction(
                lambda x: {
                    'msg': 'OK',
                    'self.cmdClass': 'AT'}))
        atParser.add(
            "Z",
            ParseAction(
                lambda x: {
                    'msg': 'OK',
                    'self.cmdClass': 'AT'}))
        atParser.add("D", ParseAction(self.doDial))
        atParser.add(
            "I",
            ParseAction(
                lambda x: {
                    'msg': 'pyDriveWire %s\r\nOK' % self.server.version,
                    'self.cmdClass': 'AT'}))
        atParser.add(
            "O",
            ParseAction(
                lambda x: {
                    'msg': 'OK',
                    'self.cmdClass': 'AT'}))
        atParser.add(
            "H",
            ParseAction(
                lambda x: {
                    'msg': 'OK',
                    'self.cmdClass': 'AT'}))
        atParser.add(
            "E",
            ParseAction(
                lambda x: {
                    'msg': 'OK',
                    'self.cmdClass': 'AT',
                    'self.echo': True}))

        uiSFileParser = ParseNode("file")
        uiSFileParser.add("defaultdir", ParseAction(self.doUSFdefaultdir))
        uiSFileParser.add("dir", ParseAction(self.doUSFdir))
        uiSFileParser.add("info", ParseAction(self.doUSFinfo))
        uiSFileParser.add("roots", ParseAction(self.doUSFroots))
        uiSFileParser.add("xdir", ParseAction(self.doUSFxdir))

        uiServerParser = ParseNode("server")
        uiServerParser.add("file", uiSFileParser)

        uiParser = ParseNode("ui")
        uiParser.add("server", uiServerParser)

        mcAliasParser = ParseNode("alias")
        mcAliasParser.add("show", ParseAction(self.doMcAliasShow))
        mcAliasParser.add("add", ParseAction(self.doMcAliasAdd))
        mcAliasParser.add("remove", ParseAction(self.doMcAliasRemove))

        mcParser = ParseNode("mc")
        mcParser.add("alias", mcAliasParser)
        mcParser.add("setdir", ParseAction(self.doMcSetDir))
        mcParser.add("getdir", ParseAction(self.doMcGetDir))
        mcParser.add("listdir", ParseAction(self.doMcListDir))
        mcParser.add("show", ParseAction(self.doShow))
        mcParser.add("eject", ParseAction(self.doEject))

        dloadAliasParser = ParseNode("alias")
        dloadAliasParser.add("show", ParseAction(self.doDloadAliasShow))
        dloadAliasParser.add("add", ParseAction(self.doDloadAliasAdd))
        dloadAliasParser.add("remove", ParseAction(self.doDloadAliasRemove))

        dloadParser = ParseNode("dload")
        dloadParser.add("alias", dloadAliasParser)
        dloadParser.add("status", ParseAction(self.doDloadStatus))
        dloadParser.add("enable", ParseAction(self.doDloadEnable))
        dloadParser.add("disable", ParseAction(self.doDloadDisable))
        dloadParser.add("setdir", ParseAction(self.doDloadSetDir))
        dloadParser.add("getdir", ParseAction(self.doDloadGetDir))
        dloadParser.add("listdir", ParseAction(self.doDloadListDir))
        dloadParser.add("translate", ParseAction(self.doDloadTranslate))

        nobjAliasParser = ParseNode("alias")
        nobjAliasParser.add("show", ParseAction(self.doNamedObjAliasShow))
        nobjAliasParser.add("add", ParseAction(self.doNamedObjAliasAdd))
        nobjAliasParser.add("remove", ParseAction(self.doNamedObjAliasRemove))

        nobjParser = ParseNode("namedobj")
        nobjParser.add("alias", nobjAliasParser)
        nobjParser.add("setdir", ParseAction(self.doNamedObjSetDir))
        nobjParser.add("getdir", ParseAction(self.doNamedObjGetDir))
        nobjParser.add("listdir", ParseAction(self.doNamedObjListDir))
        nobjParser.add("show", ParseAction(self.doShow))
        nobjParser.add("eject", ParseAction(self.doEject))

        self.parseTree = ParseNode("")
        self.parseTree.add("dw", dwParser)
        self.parseTree.add("tcp", tcpParser)
        self.parseTree.add("AT", atParser)
        self.parseTree.add("ui", uiParser)
        self.parseTree.add("mc", mcParser)
        self.parseTree.add("dload", dloadParser)
        self.parseTree.add("namedobj", nobjParser)
        self.parseTree.add("telnet", ParseAction(self.doTelnet))
        self.parseTree.add("ssh", ParseAction(self.doSsh))
        self.parseTree.add("help", ParseAction(self.ptWalker))
        self.parseTree.add("pwd", ParseAction(self.doPwd))
        self.parseTree.add("?", ParseAction(self.ptWalker))

    def __init__(self, server):
        self.server = server
        self.setupParser()

    def doInsert(self, data):
        opts = data.split(' ')
        usageMsg = "dw disk insert <drive> <path> [<opts>]"
        if len(opts) < 2:
            raise Exception('Usage: '+usageMsg)
        drive = opts[0]
        try:
            _ = int(drive)
        except:
            raise Exception("Invalid drive: %s\r\nUsage: %s" % (drive, usageMsg))
        pathStart = len(drive) + 1
        pathEnd = len(data)
        stream = False
        mode = 'rb+'
        raw = False
        proto = 'dw'
        dosplus = None
        for s in opts[2:]:
            if s.lower() == '--stream':
                stream = True
                pathEnd -= 9  # len(' --stream')
            elif s.lower() == '--ro':
                mode = 'r'
                pathEnd -= 5  # len(' --ro')
            elif s.lower() == '--raw':
                raw = True
                pathEnd -= 6  # len(' --raw')
            elif s.lower() == '--dw':
                proto = 'dw'
                pathEnd -= 5  # len(' --dw')
            #elif s.lower() == '--mc':
            #    proto = 'mc'
            #    pathEnd -= 5  # len(' --mc')
            elif s.lower() == '--dload':
                proto = 'dload'
                raw = True
                pathEnd -= 8  # len(' --dload')
            elif s.lower() == '--namedobj':
                proto = 'namedobj'
                raw = True
                pathEnd -= 11  # len(' --namedobj')
            elif s.lower() == '--dosplus':
                dosplus = True
                pathEnd -= 10  # len(' --dosplus')
        path = data[pathStart:pathEnd]
        try:
            self.server.open(int(drive), path, mode=mode, stream=stream, raw=raw, proto=proto, dosplus=dosplus)
        except Exception as e:
            return str(e)
        return "open(%d, %s)" % (int(drive), path)

    def doDiskCreate(self, data):
        usageMsg = "dw disk create <drive> <path> [<opts>]"
        opts = data.split(' ')
        if len(opts) < 2:
            raise Exception(usageMsg)
        drive = opts[0]
        try:
            _ = int(drive)
        except:
            raise Exception("Invalid drive: %s\r\nUsage: %s" % (drive, usageMsg))
        pathStart = len(drive) + 1
        pathEnd = len(data)
        stream = False
        mode = 'ab+'
        path = data[pathStart:pathEnd]
        self.server.open(int(drive), path, mode=mode, stream=stream, create=True, proto='dw')
        return "create(%d, %s)" % (int(drive), path)


    def doDiskInfo(self, data):
        opts = data.split(' ')
        usageMsg = "dw disk info <drive>"
        if len(opts) < 1:
            raise Exception(usageMsg)
        try:
           drive = int(opts[0])
        except:
            raise Exception("Invalid drive: %s\r\nUsage: %s" % (opts[0], usageMsg))
        fi = self.server.files[drive]
        if fi is None:
            return "Drive %d: Not inserted" % drive
        out = [
            'Drive: %d' % drive,
            'Path: %s' % fi.file.name,
            'Size: %d' % fi.img_size,
            'Sectors: %d' % fi.img_sectors,
            'MaxLsn: %d' % fi.maxLsn,
            'Format: %s' % fi.fmt,
            'Offset: %s' % fi.offset,
            'Byte Offset: %s' % fi.byte_offset,
            'Proto: %s' % fi.proto,
            'flags: mode=%s, remote=%s stream=%s raw=%s dosplus=%s' % (fi.mode, fi.remote, fi.stream, fi.raw, fi.dosplus)
        ]
        return '\r\n'.join(out)

    def doReset(self, data):
        try:
           drive = int(data.split(' ')[0])
        except:
           raise Exception("dw disk reset <drive>")
        dl = len(self.server.files)
        if drive >= dl:
            raise Exception('Drive higher than maximum %d' % dl)
        if self.server.files[drive] is None:
            return "Drive %d not mounted" % drive
        self.server.reset(drive)
        return "reset(%d, %s)" % (int(drive), self.server.files[drive].name)

    def doEject(self, data):
        try:
            drive = int(data.split(' ')[0])
        except:
            raise Exception("Usage: dw disk eject <drive>")
        dl = len(self.server.files)
        if drive >= dl:
            raise Exception('Drive higher than maximum %d' % dl)
        if self.server.files[drive] is None:
            return "Drive %d not mounted" % drive
        self.server.close(drive)
        return "close(%d)" % (drive)

    def doHdbDos(self, data):
        data = data.lstrip().rstrip()
        if data:
           if data.startswith(('1', 'on', 't', 'T', 'y', 'Y')):
               self.server.hdbdos = True
           elif data.startswith(('0', 'off', 'f', 'F', 'n', 'N')):
               self.server.hdbdos = False
           else:
               raise Exception("dw server hdbdos [0|1|on|off|t|T|f|F|y|Y|n|N]")
        return "hdbdos=%s" % (self.server.hdbdos)

    def doDiskOffset(self, data):
        dp = data.split(' ')
        usageMsg = 'dw disk offset <drive> <offset>'
        if len(dp) <2:
            raise Exception('Usage: %s' % usageMsg)
        try:
           drive = int(dp[0])
        except:
           raise Exception("Invalid drive: %s\r\nUsage: %s" % (dp[0], usageMsg))
        dl = len(self.server.files)
        if drive >= dl:
            raise Exception('Drive higher than maximum %d' % dl)
        if self.server.files[drive] is None:
            return "Drive %d not mounted" % drive
        offset = self.server.files[drive].offset
        if len(dp) >= 2:
            try:
                offset = eval(dp[1])
                self.server.files[drive].offset = offset
            except BaseException:
                return "Invalid offset: %s" % (hex(offset))
        return "drive(%d) offset(%s)" % (drive, hex(offset))

    def doDosPlus(self, data, server=False):
        if server:
           usageStr = "Usage: dw server dosplus [0|1|on|off|t|T|f|F|y|Y|n|N]"
           opt = 0
           nopts = 1
        else:
           usageStr = "Usage: dw disk dosplus <drive> [0|1|on|off|t|T|f|F|y|Y|n|N]"
           opt = 1
           nopts = 2
        dp = data.split(' ')
        if not server and (len(dp) < 1 or len(dp) > 2):
            raise exception('Usage: '+usageStr)
        if server:
           n = self.server.dosplus
        else:
           try:
               drive = int(dp[0])
           except:
               raise Exception("Invalid drive: %s\r\nUsage: %s" % (dp[0], usageStr))
           n = self.server.files[drive].dosplus
        if len(dp) == nopts:
            if dp[opt].startswith(('1', 'on', 't', 'T', 'y', 'Y')):
                n = True
            elif dp[opt].startswith(('0', 'off', 'f', 'F', 'n', 'N')):
                n = False
            elif not server:
                raise Exception(usageStr)
        if server:
            self.server.dosplus = n
            return "server dosplus(%s)" % (n)
        else:
            self.server.files[drive].dosplus = n
            return "drive(%d) dosplus(%s)" % (drive, n)

    def doDiskDosPlus(self, data):
        return self.doDosPlus(data, server=False)

    def doServerDosPlus(self, data):
        return self.doDosPlus(data, server=True)

    def doInstanceSelect(self, data):
        try:
            instance = int(data.split(' ')[0])
        except:
            raise Exception("dw instance select <instance>")
        if instance >= len(self.server.instances):
            return 'Invalid instance %d' % instance
        self.server = self.server.instances[instance]
        return "Selected Instance %s: %s" % (
            self.server.instance, self.server.conn.name())

    def doInstanceShow(self, data):
        out = ['', '']
        out.append("Inst.  Type")
        out.append("-----  --------------------------------------")
        i = 0
        for inst in self.server.instances:
            c = ' '
            if i == self.server.instance:
                c = '*'
            if 'instName' in inst.args:
                name = '[%s]' % inst.args.instName
            else:
                name = '(main)'
            out.append("%d%c     %s %s" % (i, c, name, inst.conn.name()))
            i += 1

        out.append('')
        return '\n\r'.join(out)

    def doPortClose(self, data):
        data = data.lstrip().rstrip()
        if not data:
           raise Exception("Usage: dw port close <portNum>")
        try:
           channel = chr(int(data))
        except:
           raise Exception("Invalid port %s" % channel)
        if channel not in self.server.channels:
            return "Invalid port %s" % channel
        ch = self.server.channels[channel]
        ch.close()
        del self.server.channels[channel]
        return "Port=n%s closing" % data

    def doPortShow(self, data):
        out = ['', '']
        out.append("Port   Status")
        out.append("-----  --------------------------------------")
        i = 0
        for i, ch in self.server.channels.items():
            co = ch.conn
            connstr = "State: %s Class: %s" % (ch.getState(), ch.cmdClass)
            # connstr = " Online" if ch.online else "Offline"
            # if co:
            # 	direction = " In" if ch.inbound else "Out"
            # 	connstr = "%s %s %s:%s" % (connstr, direction, co.host, co.port)
            out.append("N%d      %s" % (int(ord(i)), connstr))

        out.append('')
        args = self.server.args
        out.append('Term: %s Rows: %s Cols: %s' % (
            args.portTerm,
            args.portRows,
            args.portCols))
        return '\n\r'.join(out)

    def doPortDebug(self, data):
        data = data.lstrip().rstrip()
        usageStr = "Usage: dw port debug <port> [0|1|on|off|t|T|f|F|y|Y|n|N]"
        if not data:
            raise Exception(usageStr)
        dv = data.split(' ')
        if len(dv)<1 or len(dv)>2:
            raise Exception(usageStr)
        try:
           cn = dv[0]
           channel = chr(int(cn))
        except:
           raise Exception('Invalid port: %s' %cn)
        if not channel in self.server.channels:
            return "Invalid port: %s" % cn
        state = None
        if len(dv) > 1:
            state = dv[1]
        ch = self.server.channels[channel]
        if state.startswith(('1', 'on', 't', 'T', 'y', 'Y')):
            ch.debug = True
        if state.startswith(('0', 'off', 'f', 'F', 'n', 'N')):
            ch.debug = False
        return "Port=N%s debug=%s" % (cn, ch.debug)

    def doPortTerm(self, data):
        data = data.lstrip().rstrip()
        args = self.server.args
        if data:
            args.portTerm = data
        return "Terminal Type: %s" % args.portTerm

    def doPortRows(self, data):
        data = data.lstrip().rstrip()
        if data:
            try:
                int(data)
            except:
                raise Exception('Usage: dw port rows <rows>')
        args = self.server.args
        if data:
            args.portRows = int(data)
        return "Terminal Rows: %s" % args.portRows

    def doPortCols(self, data):
        data = data.lstrip().rstrip()
        if data:
            try:
                int(data)
            except:
                raise Exception('Usage: dw port cols <cols>')
        args = self.server.args
        if data:
            args.portCols = int(data)
        return "Terminal Cols: %s" % args.portCols

    # XXX: Not working
    def _doAnsiCPR(self):
        if not self.conn:
            return (1,1)
        print('doAnsiCpr')
        okChars = '\e0123456789;R['
        print('send CPR')
        self.conn.write('\e[6n')
        s = ''
        ok = True
        while ok:
            c = self.conn.read(1)
            print('read %s' % c)
            if c not in okChars:
                ok = False
            else:
                s += c
                if c =='R':
                    break
                ok = True
        print('ok=%s' % ok)
        if not ok:
            return (16,32)
        (row,col) = s.split(';')
        row = row[2:]
        col = col[:-1]
        return(row, col)

    # XXX: Not working
    def _doPortDiscoverSize(self):
        if not self.conn:
            return(16,32)
        (oldRow, oldCol) = self._doAnsiCPR()
        self.conn.write('\e[133;133H')
        (maxRow, maxCol) = self._doAnsiCPR()
        self.conn.write('\e%d;%dH' % (oldRow, oldCol))
        return (maxRow, maxCol)

    # XXX: Not working
    def doPortSize(self, data):
        data = data.lstrip().rstrip()
        args = self.server.args
        if data:
            p = data.split(' ')
            if p[0] == 'auto':
                args.portSize = p[0]
            elif len(p) == 2:
                args.portSize = None
                args.portRows = int(p[0])
                args.portCols = int(p[1])
            elif len(p) > 2:
                raise Exception('Usage: dw port size auto | <rows> <cols>')
        if args.portSize == 'auto':
            (args.portRows, args.portCols) = self._doPortDiscoverSize()
            msg = 'auto: rows=%d cols=%d' % (args.portRows, args.portCols)
        elif args.portRows and args.portCols:
            msg = 'rows=%d cols=%d' % (args.portRows, args.portCols)
        return "Terminal Size: %s" % msg

    def doShow(self, data):
        out = ['', '']
        out.append("Drive  File")
        out.append("-----  --------------------------------------")
        i = 0
        # for f in self.server.files[:4]:
        for f in self.server.files:
            if i >= 4 and f is None:
                i += 1
                continue
            name = f.name if f else f
            if f and f.remote:
                name += '(%s)' % f.file.name
            out.append("%-3d    %s" % (i, name))
            i += 1

        out.append('')
        return '\n\r'.join(out)

    def doConnDebug(self, data):
        data = data.lstrip().rstrip()
        if data.startswith(('1', 'on', 't', 'T', 'y', 'Y')):
            self.server.conn.debug = True
        elif data.startswith(('0', 'off', 'f', 'F', 'n', 'N')):
            self.server.conn.debug = False
        elif data:
           raise Exception("Usage: dw server conn debug [0|1|on|off|t|T|f|F|y|Y|n|N]")
        return "connDebug=%s" % (self.server.conn.debug)

    def doTimeout(self, data):
        opts = data.lstrip().rstrip().split(' ')
        if opts:
            try:
               timeout = float(opts[0])
            except:
               raise Exception("Invalid timeout: %s" % data)
            self.server.timeout = timeout
        return "timeout=%s" % (self.server.timeout)

    def doVersion(self, data):
        return "pyDriveWire Server %s" % self.server.version

    def doDebug(self, data):
        out = []
        if data.startswith(('on', 't', 'T', 'y', 'Y')):
            self.server.debug = True
        elif data.startswith(('off', 'f', 'F', 'n', 'N')):
            self.server.debug = False
        elif data and data[0].isdigit():
            d = int(data[0])
            self.server.debug = d
            if d == 2:
                out += [self.doConnDebug('1')]
            elif d < 2:
                out += [self.doConnDebug('0')]
            else:
                raise Exception("dw server debug [T|f|F|F|Y|y|N|n|0|1|2|on|off]")
        elif data:
            raise Exception("dw server debug [T|f|F|F|Y|y|N|n|0|1|2|on|off]")
        out += ["debug=%s" % (self.server.debug)]
        return '\r\n'.join(out)

    # def doDir(self, data, nxti):
    def doDir(self, data, msg=None):
        out = ['']
        if msg is not None:
           out += msg
        # print "doDir data=(%s)" % data
        if not data:
            data = os.getcwd()
        out.extend(os.listdir(os.path.expanduser(data)))
        out.append('')
        return '\n\r'.join(out)

    def doList(self, path, msg=None):
        out = []
        if msg is not None:
           out += msg
        # cmd = ['cat']
        # path = data.split(' ')[0]
        path = path.lsplit().rsplit()
        if not path:
            raise Exception("Usage: dw server list <path>")
        # cmd.append(path)
        # data2 = subprocess.Popen(
        # 	" ".join(cmd),
        # 	stdout=subprocess.PIPE,
        # 	stderr=subprocess.STDOUT,
        # 	shell=True)
        # out.extend(data2.stdout.read().strip().split('\n'))
        out.extend(open(os.path.expanduser(path)).read().split('\n'))
        # out.append('')
        return '\n\r'.join(out)

    def doSsh(self, data):
        return self.doConnect(data, ssh=True, interactive=True)

    def doTelnet(self, data):
        return self.doConnect(data, telnet=True, interactive=True)

    def doDial(self, data):
        return self.doConnect(data, telnet=False, ssh=False, interactive=True)

    def doConnect(self, data, telnet=False, ssh=False, interactive=False):
        pr = urlparse.urlparse(data)
        args = self.server.args
        if pr.scheme == 'ssh':
            ssh = True
        if ssh:
            if (not args.experimental) or (args.experimental and 'ssh' not in args.experimental):
                raise Exception("Ssh is not enabled, use: -x ssh")

        if pr.scheme == 'telnet':
            d2 = pr.netloc
            telnet = True
        # elif pr.scheme == '':
        elif pr.scheme == 'ssh':
            ssh = True
            if not all([pr.username, pr.password, pr.hostname]):
                raise Exception('Invalid URI: ssh://<username>:<password>@<hostname>[:<port>]')
            try:
                int(pr.port)
            except BaseException:
                raise Exception('Invalid URI: ssh://<username>:<password>@<hostname>[:<port>]')
            if pr.port:
                hp = "%s:%s" % (pr.hostname, pr.port)
            else:
                hp = pr.hostname
            d2 = "%s %s %s" % (hp, pr.username, pr.password)
        else:
            d2 = data
        host = port = username = password = None
        if ssh:
            p = d2.split(' ')
            if len(p) != 3:
                raise Exception("Usage: ssh <hostname>[:<port>] <username> <password>")
            (hp, username, password) = p
            hpp = hp.split(':')
            host = hpp[0]
            if len(hpp) == 1:
                port = '22'
            else:
                port = hpp[1]
            print("host (%s)" % host)
            print("port (%s)" % port)
            print("username (%s)" % username)
            l = len(password)
            print("password (%s)[%d]" % ('*' * l, l))
        else:
            r = d2.split(':')
            if len(r) == 1:
                r = d2.split(' ')
            if len(r) == 1:
                r.append('23')
            (host, port) = r
            print "host (%s)" % host
            print "port (%s)" % port
            try:
                int(port)
            except BaseException:
                port = None
            if not host or not port:
                if pr.scheme == 'telnet':
                    raise Exception("Usage: telnet://<hostname>[:<port>]")
                elif telnet:
                    raise Exception("Usage: telnet <hostname> [<port>]")
                elif interactive:
                    raise Exception("Usage: ATD<hostname>[:<port>]")
                else:
                    raise Exception("Usage: tcp connect <hostname> [<port>]")
        try:
            if telnet:
                sock = DWTelnet(host=host, port=port, debug=self.server.debug)
            elif ssh:
                from dwssh import DWSsh
                args = self.server.args
                sock = DWSsh(
                        host,
                        username,
                        password,
                        port=port,
                        args=self.server.args,
                        debug=self.server.debug)
            else:
                sock = DWSocket(host=host, port=port, debug=self.server.debug)
            if telnet or interactive:
                res = {
                    'msg': '\r\nCONNECTED',
                    'obj': sock,
                    'self.cmdClass': 'AT',
                    'self.online': True}
            else:
                res = {
                    'msg': None,
                    'obj': sock,
                    'self.cmdClass': 'TCP'}
            sock.connect()
        except Exception as ex:
            if telnet or interactive:
                res = {'msg': '\r\nFAIL %s' % str(ex), 'self.cmdClass': 'AT'}
            else:
                res = "FAIL %s" % str(ex)
        return res

    def doListen(self, data):
        r = data.split(' ')
        port = r[0]
        return DWSocketListener(port=port)

    def doKill(self, data):
        # r = data.split(':')
        conn = self.server.connections.get(data, None)
        if not conn:
            raise Exception("Invalid connection: %s" % data)
        res = "OK killing connection %s\r\n" % data
        print res
        conn.binding = None
        conn.close()
        del self.server.connections[r]
        return res

    def doJoin(self, data):
        # r = data.split(':')

        conn = self.server.connections.get(data, None)
        print "Binding %s to %s" % (conn, data)
        if not conn:
            raise Exception("Invalid connection: %s" % data)
        conn.binding = data
        return conn

    def dumpstacks(self, data):
        import threading
        import sys
        import traceback
        id2name = dict([(th.ident, th.name) for th in threading.enumerate()])
        code = []
        for threadId, stack in sys._current_frames().items():
            code.append("\n# Thread: %s(%d)" %
                        (id2name.get(threadId, ""), threadId))
            for filename, lineno, name, line in traceback.extract_stack(stack):
                code.append(
                    'File: "%s", line %d, in %s' %
                    (filename, lineno, name))
                if line:
                    code.append("  %s" % (line.strip()))
        return "\r\n".join(code)

    def doUSFdir(self, data):
        r = []
        if os.path.isdir(data):
            dd = [os.path.join(data, d) for d in listdir(data)]
        else:
            dd = [data]
        for path in dd:
            rr = [os.path.sep]
            rr += [path]
            rr += [data]
            s = os.stat(path)
            rr += ["%d" % s.st_size]
            rr += ["%d" % s.st_mtime]
            rr += ["true" if os.path.isdir(path) else "false"]  # readable
            rr += ["false"]  # writable
            re = '|'.join(rr)
            r.append(re)
        return '\n'.join(r)

    def doUSFdefaultdir(self, data):
        raise Exception("Command not implemented")

    def doUSFinfo(self, data):
        raise Exception("Command not implemented")

    def doUSFroots(self, data):
        r = []
        if os.name == 'posix':
            r += ["/"]
        else:
            from win32com.client import Dispatch
            fso = Dispatch('scripting.filesystemobject')
            for i in fso.Drives:
                r += [i]
        return "\n".join(r)

    def doUSFxdir(self, data):
        import stuct
        r = []
        if os.path.isdir(data):
            dd = [os.path.join(data, d) for d in listdir(data)]
        else:
            dd = [data]
        for path in dd:
            s = os.stat(data)
            mt = time.localtime(s.st_mtime)
            e = struct.pack(
                ">IBBBBBBBB",
                s.st_size & 0xffffffff,
                mt[0],  # tm_year
                mt[1],  # tm_mon
                mt[2],  # tm_mday
                mt[3],  # tm_hour
                mt[4],  # tm_min
                os.path.isdir(path),
                os.access(path, W_OK),
                len(data)
            )
            e += data
            r += [e]
        return '\n'.join(r)

    def doSetDir(self, data, proto):
        data = os.path.expanduser(data.lstrip().rstrip())
        protoCmd = proto if proto != 'dw' else 'dw server'
        if len(data) == 0:
            raise Exception("Usage: %s setdir <path>" % protoCmd)
        self.server.dirs[proto] = data
        return "%s SetDir: %s" % (proto, data)

    def doGetDir(self, data, proto):
        data = ''
        try:
            data = self.server.dirs[proto]
        except Exception as e:
            return str(e)
        return "%s GetDir: %s" % (proto, data)

    def doListDir(self, data, proto):
        d = self.server.dirs[proto]
        msg = [
            '==== %s Dir: %s  ===' % (proto, d),
        ]
        return self.doDir(d, msg=msg)

    def doMcSetDir(self, data):
        return self.doSetDir(data, 'mc')

    def doMcGetDir(self, data):
        return self.doGetDir(data, 'mc')

    def doMcListDir(self, data):
        return self.doListDir(data, 'mc')

    def doDwSetDir(self, data):
        return self.doSetDir(data, 'dw')

    def doDwGetDir(self, data):
        return self.doGetDir(data, 'dw')

    def doAliasShow(self, data, proto):
        r = [proto+' Aliases',
             '==============']
        for k, v in self.server.aliases[proto].items():
            r.append("Alias: %s Path: %s" % (k, v))
        return '\n'.join(r)

    def doAliasAdd(self, data, proto):
        data = data.lstrip().rstrip()
        protoCmd = proto if proto != 'dw' else 'dw server'
        idx = data.find(' ')
        if idx == -1 or len(data) == 0:
            return "%s alias add <name> <path>" % protoCmd
        alias = data[:idx].upper()
        path = data[idx + 1:]
        self.server.aliases[proto][alias] = path
        r = ['Add %s Alias' % proto,
             '==============',
             'Alias: %s Path: %s' % (alias, path)
             ]
        return '\n'.join(r)

    # XXX ???
    #def doAliasRemove(self, data, proto):
    #    data = data.lstrip().rstrip()
    def doDwSetDir(self, data):
        return self.doSetDir(data, 'dw')

    def doDwGetDir(self, data):
        return self.doGetDir(data, 'dw')

    def doAliasShow(self, data, proto):
        r = [proto+' Aliases',
             '==============']
        for k, v in self.server.aliases[proto].items():
            r.append("Alias: %s Path: %s" % (k, v))
        return '\n'.join(r)

    def doAliasAdd(self, data, proto):
        data = data.lstrip().rstrip()
        protoCmd = proto if proto != 'dw' else 'dw server'
        idx = data.find(' ')
        if idx == -1 or len(data) == 0:
            return "%s alias add <name> <path>" % protoCmd
        alias = data[:idx].upper()
        path = data[idx + 1:]
        self.server.aliases[proto][alias] = path
        r = ['Add %s Alias' % proto,
             '==============',
             'Alias: %s Path: %s' % (alias, path)
             ]
        return '\n'.join(r)

    def doAliasRemove(self, data, proto):
        data = data.lstrip().rstrip()
        protoCmd = proto if proto != 'dw' else 'dw server'
        if len(data) == 0:
            return "%s alias remove <name>" % protoCmd
        alias = data.upper()
        path = self.server.aliases[proto].get(alias, None)
        if not path:
            return "%s: Alias %s doesn't exit" % (proto, alias)
        r = ['Remove %s Alias' % proto,
             '==============',
             'Alias: %s Path: %s' % (alias, path)
             ]
        del self.server.aliases[proto][alias]
        return '\n'.join(r)

    def doMcAliasShow(self, data):
      return self.doAliasShow(data, 'mc')

    def doMcAliasAdd(self, data):
      return self.doAliasAdd(data, 'mc')

    def doMcAliasRemove(self, data):
      return self.doAliasRemove(data, 'mc')

    def doPrintFlush(self, data):
        if self.server.vprinter:
            self.server.vprinter.printFlush()
            return("Print buffer flushed")

    def doPrintFormat(self, data):
        if self.server.vprinter:
            if data.lower() in ['pdf', 'txt']:
                self.server.vprinter.printFormat = data
        return "printFormat=%s" % (self.server.vprinter.printFormat)

    def doPrintFile(self, data):
        if self.server.vprinter:
            if self.server.vprinter.printDir is not None:
                return "ERROR: Can't use file and dir output at the same time"
            if data.lower() in ['0', 'off', 'false', 'no', 'default']:
                data = None
            self.server.vprinter.printFile = data
        return "printFile=%s" % (self.server.vprinter.printFile)

    def doPrintDir(self, data):
        if self.server.vprinter:
            if self.server.vprinter.printFile is not None:
                return "ERROR: Can't use file and dir output at the same time"
            if data.lower() in ['0', 'off', 'false', 'no', 'default']:
                self.server.vprinter.printDir = None
            if data.lower() in ['default']:
                self.server.vprinter.printDir = '/tmp' if platform.system() == 'Darwin' else tempfile.gettempdir()
            elif os.path.exists(data):
                self.server.vprinter.printDir = data
        return "printDir=%s" % (self.server.vprinter.printDir)

    def doPrintPrefix(self, data):
        if self.server.vprinter:
            if data.lower() in ['0', 'off', 'false', 'no', 'default']:
                self.server.vprinter.printPrefix = 'cocoprints'
            else:
                self.server.vprinter.printPrefix = data
        return "printCmd=%s" % (self.server.vprinter.printPrefix)

    def doPrintCmd(self, data):
        if self.server.vprinter:
            if data.lower() in ['0', 'off', 'false', 'no', 'default']:
                self.server.vprinter.printCmd = None
            else:
                self.server.vprinter.printCmd = data
        return "printCmd=%s" % (self.server.vprinter.printCmd)

    def doPrintStatus(self, data):
        vp = self.server.vprinter
        status = "Enabled" if vp else "Disabled"
        out = ["pyDriveWire Print Engine Status: %s" % status]
        if vp:
            out += ["   Output Format: %s" % vp.printFormat]
            if vp.printFile is not None:
                d = None
                f = vp.printFile
            elif vp.printDir is not None:
                d = vp.printDir
                f = None
            else:
                d = "temporary dir"
                f = "temporary file"
            out += ["   Output Directory: %s" % (d)]
            out += ["   File Prefix: %s" % (vp.printPrefix)]
            out += ["   Output File: %s" % (f)]
            out += ["   Output Command: %s" % (vp.printCmd)]
            out += ["   Current Print Buffer: %s" %
                    (vp.source_file_name if vp.source_file_name else "Not open")]

        return '\n\r'.join(out)

    def genConfigForServer(self, server=None):
        out = []
        if server is None:
            server = self.server
        args = server.args.__dict__
        instance = args.get('instance', 0)
        if instance > 0:
            out += ['', '[%s]' % args['instName']]
        for k, v in args.items():
            if k in ['files', 'cmds', 'instances', 'config', 'instance', 'instName', 'daemon']:
                continue
            if instance > 0 and k in ['experimental', 'uiPort', 'daemonStatus', 'daemonStop', 'daemonPidFile', 'daemonLogFile']:
                continue
            if k == 'hdbdos':
                v = server.hdbdos
            if k in ['hdbdos', 'dosplus']:
                v = eval("server.%s" % k)
            elif k == 'debug':
                v = server.debug
            elif k == 'offset' and v == '0':
                v = None
            if server.dload:
                out += ['option dloadEnable True']
            if v not in [None, False]:
                out += ["option %s %s" % (k, v)]
        i = 0
        for d in server.files:
            if d:
                flags=''
                if d.dosplus:
                    flags += ' --dosplus'
                elif d.raw:
                    flags += ' --raw'
                elif d.stream:
                    flags += ' --stream'
                out += ["dw disk insert %d %s%s" % (i, d.name, flags)]
            i += 1
        for pkey in ['mc', 'dload', 'namedobj']:
           for k in server.aliases[pkey]:
               out += ["%s alias add %s %s" % (pkey, k, server.aliases[pkey][k])]
        #for k in server.aliases['emcee']:
        #    out += ["mc alias add %s %s" % (k, server.emCeeAliases[k])]
        #for k in server.aliases['dload']:
        #    out += ["dload alias add %s %s" % (k, server.emCeeAliases[k])]
        #for k in server.aliases['namedobj']:
        #    out += ["namedobj alias add %s %s" % (k, server.emCeeAliases[k])]
        return out
        return out

    def genConfig(self):
        out = []
        server = self.server
        for instance in server.instances:
            out += self.genConfigForServer(instance)
        return out

    def doConfigShow(self, data):
        out = self.genConfig()
        return '\n\r'.join(out)

    def doConfigSave(self, data):
        out = self.genConfig()
        outFile = data
        if not outFile:
            outFile = self.server.args.config
        with open(os.path.expanduser(outFile), 'w') as f:
            f.write('\n'.join(out))
        return "Config Saved to: %s" % outFile

    def ptWalker(self, data):
        def walkPt(pt, nodes=[]):
            nl = []
            # nodes += [pt.name]
            for name, node in pt.nodes.items():
                # print pt.name, name
                if isinstance(node, ParseNode):
                    nl += walkPt(node, nodes + [name])
                else:
                    joiner = ' '
                    if nodes and nodes[0] == 'AT':
                        joiner = ''
                    nl.append(joiner.join(nodes + [name]))
                # print nl
            return nl
        return '\r\n'.join(walkPt(self.parseTree))

    def doDloadStatus(self, data):
        msg = []
        server = self.server
        args = server.args
        if server.dload:
            msg.append('DLOAD Enabled')
            if isinstance(server.conn, DWSerial):
                msg.append('DLOAD Speed: %s' % (server.args.dloadSpeed))
        else:
            msg.append('DLOAD Disabled')
        if args.dloadTranslate:
                msg.append('EOL Translation Enabled')
        else:
                msg.append('EOL Translation Disabled')
        msg.append(self.doGetDir(data, 'dload'))
        return('\r\n'.join(msg))

    def doDloadEnable(self, data):
        msg = []
        server = self.server
        server.dload = True
        if data:
            server.args.dloadSpeed = data
        baud = server.args.dloadSpeed
        if isinstance(server.conn, DWSerial):
            msg.append('Setting DLOAD baud rate to %s' % (baud))
            server.conn.ser.apply_settings(
                    { 'baudrate': int(baud) })

        msg.append('DLOAD Enabled')
        return('\r\n'.join(msg))

    def doDloadDisable(self, data):
        msg = []
        server = self.server
        server.dload = False
        if isinstance(server.conn, DWSerial):
            baud = server.args.speed
            msg.append('Setting DriveWire baud rate to %s' % (baud))
            server.conn.ser.apply_settings(
                    { 'baudrate': int(baud) })

        msg.append('DLOAD Disabled')
        return('\r\n'.join(msg))

    def doDloadTranslate(self, data):
        args = self.server.args
        if data.lower() in ['1', 'on', 'true', 'yes']:
            args.dloadTranslate = True
        elif data.lower() in ['0', 'off', 'false', 'no']:
            args.dloadTranslate = False
        return "dloadTranslate=%s" % (args.dloadTranslate)

    def doDloadAliasShow(self, data):
      return self.doAliasShow(data, 'dload')

    def doDloadAliasAdd(self, data):
      return self.doAliasAdd(data, 'dload')

    def doDloadAliasRemove(self, data):
      return self.doAliasRemove(data, 'dload')

    def doDloadSetDir(self, data):
        return self.doSetDir(data, 'dload')

    def doDloadGetDir(self, data):
        return self.doGetDir(data, 'dload')

    def doDloadListDir(self, data):
        return self.doListDir(data, 'dload')

    def doNamedObjAliasShow(self, data):
      return self.doAliasShow(data, 'namedobj')

    def doNamedObjAliasAdd(self, data):
      return self.doAliasAdd(data, 'namedobj')

    def doNamedObjAliasRemove(self, data):
      return self.doAliasRemove(data, 'namedobj')

    def doNamedObjSetDir(self, data):
        return self.doSetDir(data, 'namedobj')

    def doNamedObjGetDir(self, data):
        return self.doGetDir(data, 'namedobj')

    def doNamedObjListDir(self, data):
        return self.doListDir(data, 'namedobj')

    def doPwd(self, data):
        out = [
            'Current Dir: %s' % os.getcwd(),
        ]
        for proto in ['dw', 'mc', 'dload', 'namedobj']:
            out.append('%s Dir: %s' % (proto, self.server.dirs[proto]))

        return('\r\n'.join(out))

    def parse(self, data, interact=False):
        data = data.lstrip().strip()
        data = re.subn('.\b', '', data)[0]
        data = re.subn('.\x7f', '', data)[0]
        u = data.upper()
        if u.startswith("AT"):
            tokens = ["AT"]
            t2 = u[2:]
            if t2:
                tokens.append(t2)
            else:
                return {'res': "OK", 'self.cmdClass': 'AT'}
        else:
            tokens = data.split(' ')
        p = self.parseTree
        i = 0
        for t in tokens:
            # print t
            v = p.lookup(t)
            # print v
            if v:
                i += len(t) + 1
            if isinstance(v, ParseNode):
                p = v
            elif isinstance(v, ParseAction):
                if tokens[0] == "AT":
                    callData = data[3:].lstrip()
                else:
                    callData = data[i:]
                # print callData
                res = ''
                try:
                    res = v.call(callData)
                except Exception as ex:
                    #raise
                    if interact:
                        if self.server.debug == 2:
                           raise
                    res = "FAIL %s" % str(ex)
                return res
            else:
                break

        msg = []
        if t:
            msg.append("%s: Invalid command: %s" % (p.name, t))
        msg.append(p.help())
        # msg.append('')
        return '\n\r'.join(msg)
        # raise Exception("%s: Invalid" % data)


class DWRepl:
    def __init__(self, server):
        self.server = server
        self.parser = DWParser(self.server)
        self.rt = threading.Thread(target=self.doRepl, args=())
        self.rt.daemon = True
        self.rt.start()

    def doRepl(self):
        while True:
            try:
                iprompt = ''
                if len(self.server.instances) > 1:
                    server = self.parser.server
                    iprompt = '(%d)' % server.instance
                print "pyDriveWire%s> " % iprompt,
                wdata = raw_input()
            except EOFError:
                print
                print "Bye!"
                break

            # basic stuff
            if wdata.find(chr(4)) == 0 or wdata.lower() in ["exit", "quit"]:
                # XXX Do some cleanup... how?
                print "Bye!"
                break

            try:
                wdata = re.subn('.\b', '', wdata)[0]
                wdata = re.subn('.\x7f', '', wdata)[0]
                r = self.parser.parse(wdata, True)
                print r
            except Exception as ex:
                print "ERROR:: %s" % str(ex)
                traceback.print_exc()

        self.server.conn.cleanup()
        i = 0
        for f in self.server.files:
            if f:
                self.server.close(int(i))
            i += 1
        os._exit(0)


class DWRemoteRepl:
    def __init__(self, server, port=6809):
        self.server = server
        self.cmd = DWParser(server)
        self.sock = DWSocketServer(port=port)
        self.at = threading.Thread(target=self.run, args=())
        self.at.daemon = True
        self.at.start()

    def run(self):
        while True:
            # sock.accept()
            s = self.sock.read(readLine=True)
            if len(s) > 0:
                s = s.lstrip().rstrip()
                s = re.subn('.\b', '', s)[0]
                s = re.subn('.\x7f', '', s)[0]
                if s in ['quit', 'QUIT', 'exit', 'EXIT']:
                    sock.conn.close()
                    sock.conn = None
                    break
                r = self.cmd.parse(s)
                self.sock.write(r + '\n')
        self.server.conn.cleanup()
        i = 0
        for f in self.server.files:
            if f:
                self.server.close(int(i))
            i += 1
        os._exit(0)

    def wait(self):
        self.at.join()


if __name__ == '__main__':
    r = DWRepl(None)
    r.rt.join()

# finally:
# 	cleanup()


# vim: ts=4 sw=4 sts=4 expandtab
