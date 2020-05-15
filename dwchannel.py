import threading
import Queue
from threading import Lock
import copy
from dwcommand import DWParser
import time
from dwlib import canonicalize
from dwio import DWIO
from dwsocket import *


_dwvStatesDict = {
    'DWV_S_START': 0,
    'DWV_S_DW': 1,
    'DWV_S_COMMAND': 2,
    'DWV_S_ONLINE': 3,
    'DWV_S_LISTENING': 4,
    'DWV_S_INBOUND': 5,
    'DWV_S_CLOSING': 6,
    'DWV_S_CLOSED': 7,
    'DWV_S_END': 8,
    'DWV_S_TCPOUT': 9,
    'DWV_C_AT': 'AT',
    'DWV_C_DW': 'DW',
    'DWV_C_TCP': 'TCP',
}
dwvStates = {}


for k, v in _dwvStatesDict.items():
    if isinstance(v, str):
        exec("%s = '%s'" % (k, v))
    elif isinstance(v, int):
        exec("%s = %s" % (k, v))
        dwvStates[v] = k


class DWVModem(DWIO):
    def __init__(self, server, channel, conn=None, debug=False):
        print "DWVModem __init__"
        DWIO.__init__(self, threaded=False)
        self.server = server
        self.channel = channel
        self.conn = conn
        self.inbound = False
        if self.conn:
            self.inbound = True
        self.debug = debug
        # self.online = False
        self.wbuf = ''
        self.parser = DWParser(server)
        self.connected = True
        self.cq = Queue.Queue()
        self.cmdThread = threading.Thread(target=self._cmdWorker)
        self.cmdThread.daemon = True
        # self.cmdThread.start()
        self.eatTwo = False
        self.listeners = []
        self.echo = False
        # self.cmdAutoClose = True
        self.state = DWV_S_START
        self.cmdClass = DWV_C_DW
        self.closingTime = None

    def _acceptCb(self, conn):
        print "%s: accept callback called" % self
        n = self.server.registerConn(conn)
        r = "%s %s %s" % (n, conn.port, conn.addr[0])
        reply = r + "\r"  # + r + "\r\n"
        if self.debug:
            print "reply: (%s)" % reply
        self.rq.put(reply)
        self.rb.add(len(reply))

    def _cmdWorker(self):
        if self.cq.empty():
            return
        cmd = self.cq.get(True)
        if self.debug:
            print "parser", cmd
        res = self.parser.parse(cmd)
        exact = False
        reply = "0 OK command successful\r\n"
        obj = None
        msg = None
        newState = None
        if isinstance(res, dict):
            for k, v in res.items():
                if k == 'obj':
                    obj = v
                elif k == 'msg':
                    msg = v
                else:
                    if isinstance(v, str):
                        v = "'%s'" % v
                    e = '%s=%s' % (k, v)
                    if self.debug:
                        print(e)
                    exec(e)
        if isinstance(res, str) or msg:
            if msg:
                reply = msg
            # print res
            elif res.startswith("FAIL") or res.startswith("ERROR") or res.startswith("OK"):
                reply = res
            else:
                reply += res
            if self.state == DWV_S_DW:
                newState = DWV_S_CLOSING
            # if self.cmdAutoClose and not self.online:
            #        self.connected = False
        if isinstance(
                res,
                DWSocketListener) or isinstance(
                obj,
                DWSocketListener):
            if obj:
                res = obj
            # self.online = True
            self.connected = True
            newState = DWV_S_LISTENING
            if self.debug:
                print "%s: register callback: %s" % (res, self._acceptCb)
            res.registerCb(self._acceptCb)
            res.at.start()
            self.listeners.append(res)
            r = "OK listening on port %s" % res.port
            exact = True
            reply = r + "\r"  # + r + "\r\n"
        elif isinstance(res, DWIO) or isinstance(obj, DWIO):
            if obj:
                res = obj
            # self.online = True
            if self.cmdClass == DWV_C_AT:
                newState = DWV_S_ONLINE
            elif self.cmdClass == DWV_C_TCP:
                newState = DWV_S_TCPOUT
            else:
                newState = DWV_S_DW
            self.conn = res
            b = self.conn.binding
            if b:
                reply = "OK attaching to connection %s\r" % (b)
                newState = DWV_S_INBOUND
            else:
                if not msg:
                    r = "OK connected to %s:%s" % (
                        self.conn.host, self.conn.port)
                    reply = r + "\n" + r + "\r\n"
                else:
                    reply = msg + "\r\n"

                # self.eatTwo = True
            self.conn.run()
            exact = True
        # if self.online and not exact:
        if not exact:
            reply = '\r\n' + reply + '\r\n'
        if self.debug:
            print "reply: (%s)" % reply
        self.rb.add(len(reply))
        self.rq.put(reply)
        if newState is None:
            if self.cmdClass == DWV_C_AT:
                newState = DWV_S_COMMAND
            else:
                newState = DWV_S_DW
        self.state = newState

    def write(self, data, ifs=('\r', '\n')):
        if self.debug:
            print "ch: write:", canonicalize(data)
        wdata = ''
        w = 0
        pos = -1

        if not self.eatTwo and self.state in [
                DWV_S_ONLINE, DWV_S_INBOUND,
                DWV_S_TCPOUT] and self.conn:
            if self.wbuf:
                w += self.conn.write(self.wbuf)
                self.wbuf = ''
            w += self.conn.write(data)
        else:
            if self.echo:
                self.rq.put(data)
                self.rb.add(len(data))
            self.wbuf += data
            for c in ifs:
                pos = self.wbuf.find(c)
                if pos >= 0:
                    break
            if pos < 0:
                w += len(data)
            # while pos >= 0:
            else:

                if self.eatTwo:
                    if self.debug:
                        print "ch: eating: %s" % canonicalize(
                            self.wbuf[:pos + 1])
                if self.echo:
                    self.rq.put("\r")
                    self.rb.add(1)
                wdata = self.wbuf[:pos]
                self.wbuf = self.wbuf[pos + 1:]
                w += pos + 1
                if self.debug:
                    print "wdata=(%s) wbuf=(%s)" % (wdata, self.wbuf)
                if self.eatTwo:
                    self.eatTwo = False

                else:
                    wdata = wdata.lstrip().rstrip()
                    if wdata:
                        self.cq.put(wdata)
        return w

    def read(self, rlen=None):
        d = ''
        if self._outWaiting() > 0:
            d += DWIO.read(self, rlen)
            if d:
                if self.debug:
                    print "ch:i: read:", canonicalize(d)
        elif self.conn:
            d += self.conn.read(rlen)
            if d:
                if self.debug:
                    print "ch:c: read:", canonicalize(d)
        # print "d: (%s)" % d
        return d

    def outWaiting(self):
        newState = None
        d = 0
        if self.state == DWV_S_CLOSING:
            d = self._outWaiting()
            if d < 0:
                if self.closingTime > 0:
                    self.closingTime = - 1
                else:
                    self.state = DWV_S_CLOSED
                    self.closingTime = None
        elif self.state == DWV_S_END:
            d = 0
        elif self.state == DWV_S_CLOSED:
            d = 0
            if self.closingTime is None:
                self.closingTime = 10
            if self.closingTime > 0:
                self.closingTime -= 1
            else:
                self.state = DWV_S_END
                self.closingTime = None
        elif self.state == DWV_S_COMMAND:
            d = self._outWaiting()
            if d == -1:
                newState = DWV_S_CLOSING
                self.rb.close()
                print("%s: channel closing" % self)
        elif self.state in [DWV_S_LISTENING]:
            d = self._outWaiting()
            if d == -1:
                newState = DWV_S_CLOSING
                self.rb.close()
                print("%s: channel closing" % self)
        elif self.state in [DWV_S_ONLINE, DWV_S_INBOUND, DWV_S_TCPOUT]:
            d = self._outWaiting()
            if d == -1:
                newState = DWV_S_CLOSING
                self.rb.close()
                print("%s: channel closing" % self)
            elif d == 0 and self.conn:
                d = self.conn.outWaiting()
                if d == -1:
                    if self.state != DWV_S_TCPOUT:
                        reply = "\r\nNO CARRIER\r\n"
                        self.rb.add(len(reply))
                        self.rq.put(reply)
                    if self.state in [DWV_S_INBOUND, DWV_S_TCPOUT]:
                        newState = DWV_S_CLOSING
                        self.rb.close()
                    else:
                        newState = DWV_S_COMMAND
                    d = self._outWaiting()
        elif self.state == DWV_S_DW:
            d = self._outWaiting()
            if d == 0:
                newState = DWV_S_CLOSING
                self.rb.close()
                # d = self._outWaiting()
        if self.debug:
            stateMsg = "state: %s" % dwvStates[self.state]
            if newState:
                stateMsg += "==>%s" % dwvStates[newState]
            print("%s: ow: d=%d %s" % (self, d, stateMsg))
        if newState:
            self.state = newState
        return d

    def _close(self):
        print("%s: closing" % self)
        if self.conn:
            self.conn.close()
        for c in self.listeners:
            c.close()
        self.state = DWV_S_CLOSED

    def isConnected(self):
        state = self.state not in [DWV_S_CLOSING, DWV_S_CLOSED]
        return state

    def getState(self):
        return dwvStates[self.state]


# vim: ts=4 sw=4 sts=4 expandtab


# vim: ts=4 sw=4 sts=4 expandtab
