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

        serverParser = ParseNode("server")
        serverParser.add("instance", ParseAction(self.doInstanceShow))
        serverParser.add("dir", ParseAction(self.doDir))
        serverParser.add("list", ParseAction(self.doList))
        serverParser.add("dump", ParseAction(self.dumpstacks))
        serverParser.add("debug", ParseAction(self.doDebug))
        serverParser.add("timeout", ParseAction(self.doTimeout))
        serverParser.add("version", ParseAction(self.doVersion))
        serverParser.add("hdbdos", ParseAction(self.doHdbDos))
        connParser = ParseNode("conn")
        connParser.add("debug", ParseAction(self.doConnDebug))
        serverParser.add("conn", connParser)

        portParser = ParseNode("port")
        portParser.add("show", ParseAction(self.doPortShow))
        portParser.add("close", ParseAction(self.doPortClose))
        portParser.add("debug", ParseAction(self.doPortDebug))

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

        aliasParser = ParseNode("alias")
        aliasParser.add("show", ParseAction(self.doMcAliasShow))
        aliasParser.add("add", ParseAction(self.doMcAliasAdd))
        aliasParser.add("remove", ParseAction(self.doMcAliasRemove))

        mcParser = ParseNode("mc")
        mcParser.add("alias", aliasParser)
        mcParser.add("setdir", ParseAction(self.doMcSetDir))
        mcParser.add("getdir", ParseAction(self.doMcGetDir))
        mcParser.add("show", ParseAction(self.doShow))
        mcParser.add("eject", ParseAction(self.doEject))

        self.parseTree = ParseNode("")
        self.parseTree.add("dw", dwParser)
        self.parseTree.add("tcp", tcpParser)
        self.parseTree.add("AT", atParser)
        self.parseTree.add("ui", uiParser)
        self.parseTree.add("mc", mcParser)
        self.parseTree.add("telnet", ParseAction(self.doTelnet))
        self.parseTree.add("help", ParseAction(self.ptWalker))
        self.parseTree.add("?", ParseAction(self.ptWalker))

    def __init__(self, server):
        self.server = server
        self.setupParser()

    def doInsert(self, data):
        opts = data.split(' ')
        if len(opts) < 2:
            raise Exception("dw disk insert <drive> <path> [<opts>]")
        drive = opts[0]
        pathStart = len(drive) + 1
        pathEnd = len(data)
        stream = False
        mode = 'rb+'
        for s in opts[2:]:
            if s.lower() == '--stream':
                stream = True
                pathEnd -= 9  # len(' --stream')
            elif s.lower() == '--ro':
                mode = 'r'
                pathEnd -= 5  # len(' --ro')
        path = data[pathStart:pathEnd]
        self.server.open(int(drive), path, mode=mode, stream=stream)
        return "open(%d, %s)" % (int(drive), path)

    def doDiskCreate(self, data):
        opts = data.split(' ')
        if len(opts) < 2:
            raise Exception("dw disk create <drive> <path> [<opts>]")
        drive = opts[0]
        pathStart = len(drive) + 1
        pathEnd = len(data)
        stream = False
        mode = 'ab+'
        path = data[pathStart:pathEnd]
        self.server.open(int(drive), path, mode=mode, stream=stream, create=True)
        return "create(%d, %s)" % (int(drive), path)

    def doDiskInfo(self, data):
        opts = data.split(' ')
        if len(opts) < 1:
            raise Exception("dw disk info <drive>")
        drive = int(opts[0])
        fi = self.server.files[drive]
        out = [
            'Drive: %d' % drive,
            'Path: %s' % fi.file.name,
            'Size: %d' % fi.img_size,
            'Sectors: %d' % fi.img_sectors,
            'MaxLsn: %d' % fi.maxLsn,
            'Format: %s' % fi.fmt,
            'flags: mode=%s, remote=%s stream=%s' % (fi.mode, fi.remote, fi.stream)
        ]
        return '\r\n'.join(out)

    def doReset(self, data):
        drive = int(data.split(' ')[0])
        path = self.server.files[drive].file.name
        self.server.close(drive)
        self.server.open(drive, path)
        return "reset(%d, %s)" % (int(drive), path)

    def doEject(self, data):
        drive = data.split(' ')[0]
        self.server.close(int(drive))
        return "close(%d)" % (int(drive))

    def doHdbDos(self, data):
        data = data.lstrip().rstrip()
        if data.startswith(('1', 'on', 't', 'T', 'y', 'Y')):
            self.server.hdbdos = True
        if data.startswith(('0', 'off', 'f', 'F', 'n', 'N')):
            self.server.hdbdos = False
        return "hdbdos=%s" % (self.server.hdbdos)

    def doDiskOffset(self, data):
        dp = data.split(' ')
        drive = int(dp[0])
        offset = self.server.files[drive].offset
        if len(dp) >= 2:
            try:
                offset = eval(dp[1])
                self.server.files[drive].offset = offset
            except BaseException:
                raise
                return "Invalid offset %s" % (hex(offset))
        return "drive(%d) offset(%s)" % (drive, hex(offset))

    def doInstanceSelect(self, data):
        instance = data.split(' ')[0]
        self.server = self.server.instances[int(instance)]
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
        channel = chr(int(data))
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
        return '\n\r'.join(out)

    def doPortDebug(self, data):
        dv = data.split(' ')
        cn = dv[0]
        channel = chr(int(cn))
        if not chr(int(channel)) in self.server.channels:
            return "Invalid port %s" % cn
        state = None
        if len(dv) > 1:
            state = dv[1]
        ch = self.server.channels[channel]
        if state.startswith(('1', 'on', 't', 'T', 'y', 'Y')):
            ch.debug = True
        if state.startswith(('0', 'off', 'f', 'F', 'n', 'N')):
            ch.debug = False
        return "Port=N%s debug=%s" % (cn, ch.debug)

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
        if data.startswith(('1', 'on', 't', 'T', 'y', 'Y')):
            self.server.conn.debug = True
        if data.startswith(('0', 'off', 'f', 'F', 'n', 'N')):
            self.server.conn.debug = False
        return "connDebug=%s" % (self.server.conn.debug)

    def doTimeout(self, data):
        opts = data.split(' ')
        if opts:
            timeout = float(opts[0])
            self.server.timeout = timeout
        return "debug=%s" % (self.server.timeout)

    def doVersion(self, data):
        return "pyDriveWire Server %s" % self.server.version

    def doDebug(self, data):
        out = []
        if data.startswith(('on', 't', 'T', 'y', 'Y')):
            self.server.debug = True
        if data.startswith(('off', 'f', 'F', 'n', 'N')):
            self.server.debug = False
        if data and data[0].isdigit():
            d = int(data[0])
            self.server.debug = d
            if d == 2:
                out += [self.doConnDebug('1')]
            elif d == 0:
                out += [self.doConnDebug('0')]
        out += ["debug=%s" % (self.server.debug)]
        return '\r\n'.join(out)

    # def doDir(self, data, nxti):
    def doDir(self, data):
        out = ['']
        # print "doDir data=(%s)" % data
        if not data:
            data = os.getcwd()
        out.extend(os.listdir(data))
        out.append('')
        return '\n\r'.join(out)

    def doList(self, path):
        out = []
        # cmd = ['cat']
        # path = data.split(' ')[0]
        if not path:
            raise Exception("list: Bad Path")
        # cmd.append(path)
        # data2 = subprocess.Popen(
        # 	" ".join(cmd),
        # 	stdout=subprocess.PIPE,
        # 	stderr=subprocess.STDOUT,
        # 	shell=True)
        # out.extend(data2.stdout.read().strip().split('\n'))
        out.extend(open(path).read().split('\n'))
        # out.append('')
        return '\n\r'.join(out)

    def doTelnet(self, data):
        return self.doConnect(data, telnet=True, interactive=True)

    def doDial(self, data):
        return self.doConnect(data, telnet=False, interactive=True)

    def doConnect(self, data, telnet=False, interactive=False):
        pr = urlparse.urlparse(data)
        if pr.scheme == 'telnet':
            d2 = pr.netloc
            telnet = True
        # elif pr.scheme == '':
        else:
            d2 = data
        r = d2.split(':')
        if len(r) == 1:
            r = d2.split(' ')
        if len(r) == 1:
            r.append('23')
        (host, port) = r
        print "host (%s)" % host
        print "port (%s)" % port
        if not host and not port:
            raise Exception("telnet: Bad Host/Port: %s" % data)
        try:
            if telnet:
                sock = DWTelnet(host=host, port=port, debug=self.server.debug)
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
            raise
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

    def doMcSetDir(self, data):
        try:
            os.chdir(data)
        except Exception as e:
            return str(e)
        return "chdir(%s)" % data

    def doMcGetDir(self, data):
        dir = ''
        try:
            dir = os.getcwd()
        except Exception as e:
            return str(e)
        return "Cwd: %s" % dir

    def doMcAliasShow(self, data):
        r = ['Server Aliases',
             '==============']
        for k, v in self.server.emCeeAliases.items():
            r.append("Alias: %s Path: %s" % (k, v))
        return '\n'.join(r)

    def doMcAliasAdd(self, data):
        idx = data.find(' ')
        if idx == -1:
            return "mc alias add <name> <path>"
        alias = data[:idx].upper()
        path = data[idx + 1:]
        self.server.emCeeAliases[alias] = path
        r = ['Add Alias',
             '==============',
             'Alias: %s Path: %s' % (alias, path)
             ]
        return '\n'.join(r)

    def doMcAliasRemove(self, data):
        alias = data.upper()
        path = self.server.emCeeAliases.get(alias, None)
        if not path:
            return "Alias %s doesn't exit" % alias
        r = ['Remove Alias',
             '==============',
             'Alias: %s Path: %s' % (alias, path)
             ]
        del self.server.emCeeAliases[alias]
        return '\n'.join(r)

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
            elif k == 'debug':
                v = server.debug
            elif k == 'offset' and v == '0':
                v = None
            if v not in [None, False]:
                out += ["option %s %s" % (k, v)]
        i = 0
        for d in server.files:
            if d:
                out += ["dw disk insert %d %s" % (i, d.name)]
            i += 1
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
        with open(outFile, 'w') as f:
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
                    if interact:
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
