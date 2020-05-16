import paramiko
import threading
from dwio import DWIO
import time
from dwlib import canonicalize


class DWSsh(DWIO):
    def __init__(self, host, username, password, port=22, debug=False, args=None):
        DWIO.__init__(self, threaded=True, debug=debug)
        self.host = host
        self.port = int(port)
        self.conn = None
        self.binding = None
        self.username = username
        self.password = password
        if args:
            self.term = args.portTerm
            self.rows = args.portRows
            self.cols = args.portCols
        else:
            self.term = 'ansi'
            self.rows = 16
            self.cols = 32

    def isConnected(self):
        return self.conn is not None

    def connect(self):
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.connect(self.host, port=self.port, username=self.username, password=self.password)
        self.conn = client.invoke_shell(term=self.term, height=self.rows, width=self.cols)
        self.client = client
        #self.conn = telnetlib.Telnet(self.host, self.port)
        # self.conn.set_option_negotiation_callback(self._negotiate_echo_on)

    def _read(self, count=256):
        data = ''
        if not self.isConnected():
            return data
        try:
            # data = self.conn.read_very_eager()
            #data = self.conn.read_some()
            data = ''
            # if self.conn.recv_ready():
            data = self.conn.recv(count)
            if data == '':
                raise Exception("EOF")
        except Exception as ex:
            print str(ex)
            print "ERROR: Connection Closed"
            self._close()
        if self.debug and data != '':
            print "tel read:", canonicalize(data)
        return data

    def _write(self, data):
        if not self.isConnected():
            return 0
        if self.debug and data != '':
            print "tel write:", canonicalize(data)
        try:
            self.conn.send(data)
        except Exception as ex:
            print str(ex)
            print "ERROR: Connection Closed"
            self._close()
        return len(data)

    def _close(self):
        self._print("Closing Connection...")
        try:
            self.conn.close()
            self.client.close()
        except BaseException:
            pass
        self.conn = None
        self.client = None
        self.abort = True

    '''
    def _negotiate_echo_on(self, sock, cmd, opt):
        # This is supposed to turn server side echoing on and turn other
        # options off.
        sock = self.conn.get_socket()
        if opt == telnetlib.ECHO and cmd in (telnetlib.WILL, telnetlib.WONT):
            sock.sendall(telnetlib.IAC + telnetlib.DO + opt)
        elif opt != telnetlib.NOOPT:
            if cmd in (telnetlib.DO, telnetlib.DONT):
                sock.sendall(telnetlib.IAC + telnetlib.WONT + opt)
            elif cmd in (telnetlib.WILL, telnetlib.WONT):
                sock.sendall(telnetlib.IAC + telnetlib.DONT + opt)
    '''


if __name__ == '__main__':
    import sys

    sock = DWSsh()

    def cleanup():
        # print "main: Closing sockial port."
        sock.close()
    import atexit
    atexit.register(cleanup)

    try:
        sock.connect()
        while True:
            print ">",
            wdata = raw_input()
            sock.write(wdata)
            # sock.write("\n> ")
            # print "main: Wrote %d bytes" % len(wdata)
            rdata = sock.readline()
            # print "main: Read %d bytes" % len(rdata)
            print rdata,
    finally:
        cleanup()


# vim: ts=4 sw=4 sts=4 expandtab
