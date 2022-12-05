# !/usr/local/bin/python
import socket
import threading
from dwio import DWIO
import time
import select
from dwlib import canonicalize


class DWSocket(DWIO):
    def __init__(self, host='localhost', port=6809, conn=None, addr=None, debug=False):
        DWIO.__init__(self, threaded=True)
        self.host = host
        self.port = int(port)
        self.conn = conn
        if self.conn:
            self.sock = self.conn
        else:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        self.addr = addr
        self.binding = None
        self.debug = debug

    def _print(self, msg):
        if self.debug:
            print(msg)

    def name(self):
        return "%s %s:%s" % (self.__class__, self.host, self.port)

    def isConnected(self):
        return self.conn is not None

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        self.sock.connect((self.host, self.port))
        self._print("socket: %s: connecting to %s:%s" % (self, self.host, self.port))
        self.conn = self.sock

    def _read(self, count=256):
        data = None
        if self.abort or not self.conn:
            return ''
        ri = []
        try:
            (ri, _, _) = select.select([self.conn.fileno()], [], [], 1)
        except Exception as e:
            print(str(e))
            raise Exception("%s: _read (1): Connection closed" % self)
            self._close()
        if any(ri):
            # print "dwsocket: reading"
            data = self.conn.recv(count)
        # else:
            # print "dwsocket: waiting"
        if data == '':
            raise Exception("%s: _read (2): Connection closed" % self)
            self._close()
        # if data:
        # 	print "r",data
        if self.debug and data is not None:
            self._print("\n< socket read: %s: %s" % (self, canonicalize(data)))
        return data

    def _write(self, data):
        if self.abort or not self.conn:
            return -1
        n = 0
        wi = []
        try:
            (_, wi, _) = select.select([], [self.conn.fileno()], [], 1)
        except Exception as e:
            print(str(e))
            raise Exception("%s: _write: Connection closed" % self)
            self._close()
            n = -1
        if any(wi):
            try:
                n = self.conn.send(data)
                if self.debug:
                    self._print("\n> socket write: %s: %s" % (self, canonicalize(data)))
            except Exception as e:
                print(str(e))
                self._close()
                n = -1

        return n

    def _in_waiting(self):
        if self.abort or not self.conn:
            return False
        ri = []
        try:
            (ri, _, _) = select.select([self.conn.fileno()], [], [], 1)
        except Exception as e:
            print(str(e))
            self._print("Connection closed: %s" % self)
            self._close()
        return any(ri)
        # return self.sock.in_waiting

    def _out_waiting(self):
        if self.abort or not self.conn:
            return False
        wi = []
        try:
            (_, wi, _) = select.select([], [self.conn.fileno()], [], 1)
        except Exception as e:
            print str(e)
            # print "Connection closed",self
            # self._close()
        return any(wi)
        # return self.sock.in_waiting

    def _close(self):
        # if not self.conn:
        # 	return
        ri = wi = []
        try:
            (ri, wi, _) = select.select(
                [self.conn.fileno()], [self.conn.fileno()], [], 0)
        except Exception as e:
            pass
            # print str(e)
            # print "Connection closed"
        if any(ri + wi):
            self._print("Closing: connection: %s" % self)
            try:
                # self.conn.shutdown(socket.SHUT_RDWR)
                self.conn.close()
            except BaseException:
                pass
        # if any(wi):
        # 	print "Closing socket"
        # 	try:
        # 		self.conn.shutdown(socket.SHUT_RDWR)
        # 	except:
        # 		pass
        self.conn = None
        self.abort = True
        # self.sock.shutdown(socket.SHUT_RDWR)

    def _cleanup(self):
        self.abort = True
        self._close()
        if self.sock:
            self._print("Closing: socket: %s" % self)
            try:
                self.sock.close()
            except BaseException:
                pass
            self.sock = None


class DWSocketServer(DWSocket):
    def __init__(self, host='localhost', port=6809, debug=False, closedCb=None):
        DWSocket.__init__(self, host=host, port=port, debug=debug)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('0.0.0.0', self.port))
        self.closedCb = closedCb

    def accept(self):
        while not self.abort:
            self.conn = None
            try:
                r = self.sock.listen(0)
                (self.conn, self.addr) = self.sock.accept()
                self._print("Accepted Connection: %s" % str(self.addr))
            except Exception as ex:
                print("Server Aborted", str(ex))

            if self.conn:
                break
            self._print("looping")

    def _read(self, count=256):
        data = None
        if not self.conn:
            self._print("accepting")
            self.accept()
        data = ''
        try:
            data = DWSocket._read(self, count)
        except Exception as e:
            print(str(e))
            self.conn.close()
            self.conn = None
            if self.closedCb:
                print("%s: Calling callback: %s" % (self, self.closedCb))
                self.closedCb(self)
        return data


class DWSocketListener(DWSocket):
    def __init__(self, host='localhost', port=6809, acceptCb=None, debug=False):
        DWSocket.__init__(self, host=host, port=port, debug=debug)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('0.0.0.0', self.port))
        self.connections = []
        self.at = threading.Thread(target=self._accept, args=())
        self.at.daemon = True

    def registerCb(self, cb):
        self._print("%s: Callback registration: %s" % (self, cb))
        self.acceptCb = cb

    def accept(self):
        raise Exception("Oppps, don't call me")

    def _accept(self):
        try:
            print("%s: Listening on: %s" % (self, self.port))
            r = self.sock.listen(0)
            fd = self.sock.fileno()

            while not self.abort:
                ri = []
                # print "select: %s" % fd
                (ri, _, _) = select.select([fd], [], [], 1)

                if any(ri):
                    try:
                        (sock, addr) = self.sock.accept()
                        print("%s: Accepted Connection: %s" % (self, str(addr)))
                        conn = DWSocket(conn=sock, port=self.port, addr=addr)
                        self.connections.append(conn)
                        if self.acceptCb:
                            self._print("%s: Calling Callback: %s" % (self, self.acceptCb))
                            self.acceptCb(conn)
                    except Exception as ex:
                        print("Listener socket failure, port=%s" % (self.port, str(ex)))

        except Exception as ex:
            print("Server Aborted, port=%s" % self.port, str(ex))
        finally:
            self._close()
            self.sock.close()

    def _close(self):
        self.connected = False
        self.abort = True
        self._print("%s: Closing up shop port=%s" % (self, self.port))
        for c in self.connections:
            c.close()


class DWSimpleSocket:
    def __init__(
            self,
            host='localhost',
            port=6809,
            conn=None,
            reconnect=False,
            debug=False,
            closedCb=None):
        self.host = host
        self.port = int(port)
        self.conn = conn
        self.connected = False
        self.abort = False
        if self.conn:
            self.sock = self.conn
        else:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        self.reconnect = reconnect
        self.debug = debug
        self.closedCb = closedCb

    def name(self):
        return "%s %s:%s" % (self.__class__, self.host, self.port)

    def isConnected(self):
        return self.conn is not None

    def run(self):
        pass

    def connect(self):
        while self.conn is None:
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                self.sock.connect((self.host, self.port))
                print(
                    "socket: %s: Connected to %s:%s" %
                    (self, self.host, self.port))
                self.conn = self.sock
            except BaseException:
                if self.reconnect:
                    time.sleep(1)
                else:
                    raise

    def read(self, n=1, timeout=None):
        data = ''
        while not self.abort and len(data) < n:
            d = self.conn.recv(n - len(data))
            while not self.abort and d == '' and self.reconnect:
                print("socket: %s: Disconnected" % (self))
                self.close()
                if self.closedCb:
                    print("%s: Calling callback: %s" % (self, self.closedCb))
                    self.closedCb(self)
                print(
                    "socket: %s: Reconnecting to %s:%s" %
                    (self, self.host, self.port))
                self.connect()
                d = self.conn.recv(n - len(data))
            if d != '':
                data += d
        return data

    def write(self, data):
        return self.conn.send(data)

    def close(self):
        print("socket: %s: Closing" % (self))
        if self.conn:
            self.conn.close()
            self.conn = None
        self.connected = False

    def cleanup(self):
        self.abort = True
        self.close()


if __name__ == '__main__':
    import sys

    sock = DWSocketServer()

    def cleanup():
        print "main: Closing sockial port."
        sock.close()
    import atexit
    atexit.register(cleanup)

    try:
        sock.accept()
        while True:
            print ">",
            wdata = raw_input()
            sock.write(wdata)
            sock.write("\n> ")
            # print "main: Wrote %d bytes" % len(wdata)
            rdata = sock.readline()
            # print "main: Read %d bytes" % len(rdata)
            print rdata,
    finally:
        cleanup()


# vim: ts=4 sw=4 sts=4 expandtab


# vim: ts=4 sw=4 sts=4 expandtab
