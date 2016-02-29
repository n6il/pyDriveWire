import threading
import traceback
import subprocess
from dwsocket import DWSocket

class DWParser:
	def __init__(self, server):
		self.server=server
	def doInsert(self, data):
		(drive, path) = data.split(' ')
		self.server.open(int(drive), path)
		return "open(%d, %s)" % (int(drive), path)
	def doEject(self, data):
		drive = data.split(' ')[0]
		self.server.close(int(drive))
		return "close(%d)" % (int(drive))
	def doShow(self, data):
		out = ['','']
		out.append( "Drive  File" )
		out.append( "-----  --------------------------------------" )
		i=0
		for f in self.server.files:
			out.append( "%d      %s" % (i, f.name if f else f) )
			i += 1
		
		out.append('')
		return '\n\r'.join(out)
	def doDir(self, data, nxti):
		out = ['']
		cmd = ['ls']
		if nxti != -1:
			path = data[nxti+1:].split(' ')[0]
			cmd.append(path)
		data2 = subprocess.Popen(
			" ".join(cmd),
			stdout=subprocess.PIPE,
			stderr=subprocess.STDOUT,
			shell=True)	
		out.extend(data2.stdout.read().split('\n'))
		out.append('')
		return '\n\r'.join(out)

	def doList(self, data):
		out = []
		cmd = ['cat']
		path = data.split(' ')[0]
		print "path (%s)" % path
		if not path:
			raise Exception("list: Bad Path")
		cmd.append(path)
		data2 = subprocess.Popen(
			" ".join(cmd),
			stdout=subprocess.PIPE,
			stderr=subprocess.STDOUT,
			shell=True)	
		out.extend(data2.stdout.read().strip().split('\n'))
		#out.append('')
		return '\n\r'.join(out)

	def doConnect(self, data):
		(host,port) = data.split(' ')
		print "host (%s)" % host
		print "port (%s)" % port
		if not host and not port:
			raise Exception("list: Bad Path")
		sock = DWSocket(host=host, port=port)
		sock.connect()
		return sock

	def parse(self, data):
		try:
			# XXX: Simple stupid for now, will want to write a better parser later
			if data=='':
				return ''
			i = data.find("insert")
			nxti = data.find(" ", i)
			if i >= 0 and nxti > 0:
				return self.doInsert(data[nxti+1:])
			i = data.find("eject")
			nxti = data.find(" ", i)
			if i >= 0 and nxti > 0:
				return self.doEject(data[nxti+1:])
			i = data.find("show")
			nxti = data.find(" ", i)
			if i >= 0:
				return self.doShow('')
			i = data.find("dir")
			nxti = data.find(" ", i)
			if i >= 0:
				return self.doDir(data, nxti)
			i = data.find("list")
			nxti = data.find(" ", i)
			if i >= 0 and nxti > 0:
				return self.doList(data[nxti+1:])
			i = data.find("connect")
			nxti = data.find(" ", i)
			if i >= 0 and nxti > 0:
				return self.doConnect(data[nxti+1:])
			raise Exception("Unknown Command: %s" % data)
		except Exception as ex:
			traceback.print_exc()
			return str(ex)
		
class DWRepl:
	def __init__(self, server):
		self.server = server
		self.parser = DWParser(self.server)
		self.rt = threading.Thread(target=self.doRepl, args=())
		self.rt.start()

	def doRepl(self):
		while True:
			try: 
				print "pyDriveWire> ",
				wdata = raw_input()
			except EOFError:
				print
				print "Bye!"
				break
			
			# basic stuff
			if wdata.find(chr(4)) == 0 or wdata.find("exit") == 0:
				# XXX Do some cleanup... how?
				break
			
			try:
				print self.parser.parse(wdata)
			except:
				print "ERROR"
				traceback.print_exc()

#finally:
#	cleanup()
