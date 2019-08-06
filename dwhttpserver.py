from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from urlparse import parse_qs
import cgi
import threading
from dwcommand import DWParser
import os
import tempfile
import base64

"""
class DWParser:
    def __init__(self, server):
        self.server = server

    def parse(self, data):
        return data
"""
parser = None


class GP(BaseHTTPRequestHandler):
    def _set_headers(self, ctype, response):
        self.send_response(response)
        self.send_header('Content-type', ctype)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
    # def do_HEAD(self):
    #    self._set_headers()

    def do_GET(self):
        response = 200
        path = 'ui%s' % self.path
        if self.path in ['/', '/index.html']:
            path = 'ui/pyDriveWireUi.html'
            response = 200
        elif os.path.exists(path):
            response = 200
        else:
            response = 404
        self._set_headers('text/html', response)
        if response != 200:
            self.wfile.write(
                "<html><body><h1>%d Error: Invalid location: %s</h1></body></html>" %
                (response, self.path))
            return
        # print parse_qs(self.path[2:])
        # self.wfile.write("<html><body><h1>Get Request Received!</h1></body></html>")
        with open(path) as f:
            self.wfile.write(f.read())

    def do_POST(self):
        global parser
        clen, pdict = cgi.parse_header(
            self.headers.getheader('Content-Length'))
        mtype, pdict = cgi.parse_header(self.headers.getheader('Content-Type'))
        data = self.rfile.read(int(clen))
        # print "POST path: %s" % self.path
        response = 200
        if self.path.startswith('/upload'):
            qm = self.path.find('?')
            if qm > 0:
                qd = parse_qs(self.path[qm + 1:])
                name = qd['name'][0]
                drive = qd['drive'][0]
                print "upload drive: %s name: %s" % (drive, name)
                # fileName = tempfile.mktemp(prefix=name.split('/')[-1].split('.')[0], suffix='.'+name.split('.')[-1])
                fileName = os.path.join(tempfile.gettempdir(), name)
                print fileName
                with open(fileName, 'wb') as f:
                    comma = data.index(',')
                    f.write(base64.b64decode(data[comma + 1:]))
                data = 'dw disk insert %s %s' % (drive, fileName)
                response = 200
                msg = "OK: drive:%s name:%s" % (drive, name)
            else:
                response = 404
                msg = "%d: Error: Invalid upload specification: %s" % (
                    response, self.path)
                self._set_headers('text/html', response)
                self.wfile.write(
                    "<html><body><h1>%s</h1></body></html>" %
                    (msg))
                return
        result = parser.parse(data.lstrip().rstrip()).replace('\r', '')
        self._set_headers('text/plain', response)
        self.wfile.write(result + '\n')


class DWHttpServer:
    def __init__(self, server, port):
        global parser
        self.port = port
        self.server = server
        parser = DWParser(self.server)
        self.thread = threading.Thread(
            target=self.run, args=(), kwargs={
                'port': self.port})
        self.thread.daemon = True
        self.thread.start()

    def run(self, server_class=HTTPServer, handler_class=GP, port=8088):
        server_address = ('', port)
        httpd = server_class(server_address, handler_class)
        print 'Server running at localhost:%s...' % port
        httpd.serve_forever()


"""
def start():
    t = threading.Thread(target=run, args=())
    t.daemon = True
    t.start()
    return t
t = start()
wdata = raw_input()
"""

if __name__ == '__main__':
    r = DWHttpServer(None, 8088)
    wdata = raw_input()


# vim: ts=4 sw=4 sts=4 expandtab
