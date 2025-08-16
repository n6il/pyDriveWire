#!/usr/bin/env python3

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs
import cgi
import threading
from dwcommand import DWParser
import os
import tempfile
import base64
import sys

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
        if getattr(sys, 'frozen', False):
            # we are running in a bundle
            bundle_dir = sys._MEIPASS
        else:
            # we are running in a normal Python environment
            bundle_dir = os.path.dirname(os.path.abspath(__file__))
        if self.path in ['/', '/index.html']:
            path = os.path.join(bundle_dir, "ui", 'pyDriveWireUi.html')
        else:
            path = os.path.join(bundle_dir, "ui", self.path[1:])
        if os.path.exists(path):
            response = 200
        else:
            response = 404
        self._set_headers('text/html', response)
        if response != 200:
            error_msg = ("<html><body><h1>%d Error: Invalid location: %s</h1></body></html>" %
                        (response, self.path)).encode('utf-8')
            self.wfile.write(error_msg)
            return
        # print(parse_qs(self.path[2:]))
        # self.wfile.write("<html><body><h1>Get Request Received!</h1></body></html>")

        with open(path, 'rb') as f:
            self.wfile.write(f.read())

    def do_POST(self):
        global parser
        content_length = self.headers.get('Content-Length')
        content_type = self.headers.get('Content-Type')

        if content_length:
            clen, pdict = cgi.parse_header(content_length)
        else:
            clen = 0
        if content_type:
            mtype, pdict = cgi.parse_header(content_type)

        data = self.rfile.read(int(clen))
        if isinstance(data, bytes):
            data = data.decode('utf-8')

        # print("POST path: %s" % self.path)
        response = 200
        if self.path.startswith('/upload'):
            qm = self.path.find('?')
            if qm > 0:
                qd = parse_qs(self.path[qm + 1:])
                name = qd['name'][0]
                drive = qd['drive'][0]
                print("upload drive: %s name: %s" % (drive, name))
                # fileName = tempfile.mktemp(prefix=name.split('/')[-1].split('.')[0], suffix='.'+name.split('.')[-1])
                fileName = os.path.join(tempfile.gettempdir(), name)
                print(fileName)
                with open(fileName, 'wb') as f:
                    comma = data.index(',')
                    base64_data = data[comma + 1:]
                    if isinstance(base64_data, str):
                        base64_data = base64_data.encode('utf-8')
                    f.write(base64.b64decode(base64_data))
                data = 'dw disk insert %s %s' % (drive, fileName)
                response = 200
                msg = "OK: drive:%s name:%s" % (drive, name)
            else:
                response = 404
                msg = "%d: Error: Invalid upload specification: %s" % (
                    response, self.path)
                self._set_headers('text/html', response)
                error_msg = ("<html><body><h1>%s</h1></body></html>" % msg).encode('utf-8')
                self.wfile.write(error_msg)
                return

        result = parser.parse(data.lstrip().rstrip()).replace('\r', '')
        self._set_headers('text/plain', response)
        result_bytes = (result + '\n').encode('utf-8')
        self.wfile.write(result_bytes)


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
        print('Web UI running at http://localhost:%s' % port)
        httpd.serve_forever()


"""
def start():
    t = threading.Thread(target=run, args=())
    t.daemon = True
    t.start()
    return t
t = start()
wdata = input()
"""

if __name__ == '__main__':
    r = DWHttpServer(None, 8088)
    wdata = input()


# vim: ts=4 sw=4 sts=4 expandtab
