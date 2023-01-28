# !/usr/local/bin/python
import threading
import Queue
# from collections import deque
from time import sleep


class QPC:
    def __init__(self, init=0):
        self.counter = init
        self.lock = threading.Lock()

    def add(self, i):
        self.lock.acquire()
        self.counter += i
        r = self.counter
        self.lock.release()
        return r

    def sub(self, i):
        self.lock.acquire()
        if i > self.counter:
            self.counter = 0
        else:
            self.counter -= i
        r = self.counter
        self.lock.release()
        return r

    def get(self):
        self.lock.acquire()
        r = self.counter
        self.lock.release()
        return r

    def close(self):
        self.lock.acquire()
        self.counter = -1
        r = self.counter
        self.lock.release()
        return r


class DWIO:
    def __init__(self, rwf=None, inf=None, outf=None, threaded=False, debug=False):
        self.abort = False

        if rwf:
            inf = outf = rwf
        self.inf = inf
        self.outf = outf
        self.threaded = threaded
        if self.threaded:
            self.rt = threading.Thread(target=self._readHandler, args=())
            self.rt.daemon = True
        else:
            self.rt = None
        self.rq = Queue.Queue()
        self.rb = QPC()
        self.rbuf = ''
        if self.threaded:
            self.wt = threading.Thread(target=self._writeHandler, args=())
            self.wt.daemon = True
        else:
            self.wt = None
        self.wq = Queue.Queue()
        self.connected = False
        self.debug = debug

    def _print(self, msg):
        if self.debug:
            print(msg)

    def run(self, read=True, write=True):
        if not self.threaded:
            return
        self._print("%s: Starting threads..." % self)
        self.rt.start()
        self.wt.start()

    def isConnected(self):
        return self.connected

    def outWaiting(self):
        return self._outWaiting()

    def _outWaiting(self):
        if self.rt and self.rt._Thread__stopped and self.rb.get()==0:
            print("%s: _outWaiting: closing rb(%s)=%d" % (self, self.rb, self.rb.get()))
            self.rb.close()
        n = min(214, self.rb.get())
        # print "outWaiting",n
        return n

    def readline(self, ifs='\n'):
        return self.read(readLine=True, ifs=ifs)

    def read(self, rlen=None, timeout=None, readLine=False, ifs='\n'):
        rdata = ''
        pos = -1
        _t = timeout
        if not _t:
            _t = 1
        if self.threaded and not self.abort and self.rt and not self.rt.is_alive(
        ) and not self.rt._Thread__stopped:
            # Start the background reader thread only
            # when someone asks to start reading from it
            self.rt.start()
        if self.rt and self.rt._Thread__stopped and self.rb.get()==0:
            print("%s: read:1:  closing rb(%s)=%d" % (self, self.rb, self.rb.get()))
            self.rb.close()
        if not rlen:
            d = ''
            if self.rbuf:
                d = self.rbuf
                self.rbuf = ''
            while not self.rq.empty():
                d += self.rq.get(True, _t)
            if readLine:
                pos = d.find(ifs)
                if pos >= 0:
                    self.rbuf = d[pos+1:]
                    d = d[:pos+1]
            rdata = d
        else:
            # while not self.rq.empty() or not self.abort:
            while len(rdata) < rlen:
                d = ''
                if self.rbuf:
                    d = self.rbuf
                    self.rbuf = ''
                else:
                    try:

                        d = self.rq.get(True, _t)
                    except Exception as e:
                        if timeout:
                            print str(e)
                            return ''
                        pass
                available = len(d)
                required = available
                # print rlen, len(rdata), available, len(self.rbuf)
                if not available:
                    # print "waiting2"
                    continue
                if rlen:
                    required = min(rlen - len(rdata), available)
                if readLine:
                    pos = d.find(ifs)
                    if pos >= 0:
                        required = pos + 1
                rdata += d[:required]

                if (required < available):
                    self.rbuf = d[required:]
                if readLine:
                    if pos >= 0:
                        break
                    else:
                        continue
                #if not rlen and self.rq.empty():
                #    break
                if len(rdata) == rlen:
                    break

        # print "reading: %d (%s)" %(len(rdata),rdata if ord(rdata)>32 and ord(rdata)<128 else '.')
        if self.rt and self.rt._Thread__stopped and self.rb.get()==0:
            print("%s: read:2:  closing rb(%s)=%d" % (self, self.rb, self.rb.get()))
            self.rb.close()
        self.rb.sub(len(rdata))
        return rdata

    def write(self, data):
        # print "write"
        if self.abort:
            print "w: abort"
            return 0
        if self.threaded and not self.abort and self.wt and not self.wt.is_alive(
        ) and not self.wt._Thread__stopped:
            # Start the background reader thread only
            # when someone asks to start reading from it
            self.wt.start()
        if self.wt and self.wt._Thread__stopped:
            return 0
        self.wq.put(data)
        return len(data)

    def _close(self):
        pass

    def close(self):
        self._print("%s: Closing connection" % self)
        self.abort = True
        self.rb.close()
        self._close()
        # if self.wt and self.wt.is_alive() and not self.wt._Thread__stopped:
        if self.rt:
            self.rt.abort = True
            self._print("%s: Shutting down async read thread: %s" % (self, self.rt))
            if self.rt.is_alive():
                self.rt.join()
            self.rt = None
        # if self.wt and self.wt.is_alive() and not self.wt._Thread__stopped:
        if self.wt:
            self._print("%s: Shutting down async write thread: %s" % (self, self.wt))
            self.wt.abort = True
            if self.wt.is_alive():
                self.wt.join()
            self.wt = None

    def cleanup(self):
        self._cleanup()

    def _cleanup(self):
        pass

    def _readHandler(self):
        self._print("%s: Starting _readHandler..." % self)
        while not self.abort:
            try:
                d = self._read()
            except Exception as e:
                print(str(e))
                break
            if d:
                # print "put: (%s)" % d
                self.rb.add(len(d))
                self.rq.put(d)
        self._print("%s: Exiting _readHandler...: rb=%d" % (self, self.rb.get()))

    def _read(self, rlen=None):
        data = ''
        ri = []
        try:
            (ri, _, _) = select.select([inf.fileno()], [], [], 1)
        except BaseException:
            raise
        if any(ri):
            data = self.inf.read(rlen)
        return data

    def _writeHandler(self):
        self._print("%s: Starting _writeHandler..." % self)
        while not self.abort:
            d = ''
            try:
                d = self.wq.get(True, 1)
            except Exception as e:
                pass
                # print str(e)

            if d:
                # "wh: %d" % len(d)
                self._write(d)
        self._print("%s: Exiting _writeHandler..." % self)

    def _write(self, data):
        # print "dwio._write %s" % self
        return self.outf.write(data)


class DWIOStdIo(DWIO):
    def __init__(self):
        DWIO.__init__(self, blocking=True)

    def _read(self, count=None):
        return raw_input() + '\n'

    def _write(self, data):
        sys.stdout.write(data)


if __name__ == '__main__':
    import sys
    # f=open("fifo")
    # dw=DWIO(f)
    dw = DWIOStdIo()
    while True:
        dw.write("> ")
        dw.write(dw.readline())


# vim: ts=4 sw=4 sts=4 expandtab
