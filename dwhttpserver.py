from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from urlparse import parse_qs
import cgi
import threading
from dwcommand import DWParser
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
    #def do_HEAD(self):
    #    self._set_headers()
    def do_GET(self):
	response = 200
	if self.path not in ['/', '/index.html']:
		response = 404
        self._set_headers('text/html', response)
	if response != 200:
		self.wfile.write("<html><body><h1>%d Error: Invalid location: %s</h1></body></html>" % (response, self.path))
		return
        print self.path
        #print parse_qs(self.path[2:])
        #self.wfile.write("<html><body><h1>Get Request Received!</h1></body></html>")
	with open('ui/pyDriveWireUi.html') as f:
		self.wfile.write(f.read())
    def do_POST(self):
	global parser
        self._set_headers('text/plain', 200)
	clen,pdict = cgi.parse_header(self.headers.getheader('Content-Length'))
	data = self.rfile.read(int(clen))
	if self.path.startswith('/upload'):
		qm = self.path.find('?')
		if qm > 0:
			qd = parse_qs(self.path[qm+1:])
			name = qd['name']
			fileName = tempfile.mktemp(prefix=name.split('/')[-1].split('.')[0], suffix='.'+name.split('.')[-1])
			with open(fileName, 'wb') as f:
				f.write(data)
			data = 'dw disk insert %s file://%s' % (qd['disk'], fileName)
	result = parser.parse(data.lstrip().rstrip()).replace('\r', '')
	self.wfile.write(result + '\n')

class DWHttpServer:
	def __init__(self, server, port):
		global parser
		self.port = port
		self.server = server
		parser = DWParser(self.server)
		self.thread = threading.Thread(target=self.run, args=(), kwargs={'port': self.port})
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

