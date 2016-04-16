import threading
import traceback
import subprocess
from dwsocket import DWSocket
import os

class ParseNode:
	def __init__(self, name, nodes=None):
		self.name = name
		self.nodes = {}
		if nodes:
			self.nodes = nodes
	def add(self, key, val):
		self.nodes[key]=val

	def lookup(self, key):
		return self.nodes.get(key, None)

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
		return ParseNode.lookup(self, k)

	def help(self):
		#if self.name:
		#	p.append(self.name)
		p=["commands:"]
		p.extend(["AT%s"%k for k in self.nodes])
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
		diskParser=ParseNode("disk")
		diskParser.add("insert", ParseAction(self.doInsert))
		diskParser.add("eject", ParseAction(self.doEject))
		diskParser.add("show", ParseAction(self.doShow))

		serverParser=ParseNode("server")
		serverParser.add("instance", ParseAction(self.doInstance))
		serverParser.add("dir", ParseAction(self.doDir))
		serverParser.add("list", ParseAction(self.doList))

		dwParser=ParseNode("dw")
		dwParser.add("disk", diskParser)
		dwParser.add("server", serverParser)

		tcpParser=ParseNode("tcp")

		atParser=ATParseNode("AT")
		atParser.add("", ParseAction(lambda x: "OK"))
		atParser.add("Z", ParseAction(lambda x: "OK"))
		atParser.add("D", ParseAction(lambda x: "OK"))
		atParser.add("I", ParseAction(lambda x: "pyDriveWire\nOK"))

		self.parseTree=ParseNode("")
		self.parseTree.add("dw", dwParser)
		self.parseTree.add("tcp", tcpParser)
		self.parseTree.add("AT", atParser)

	def __init__(self, server):
		self.server=server
		self.setupParser()

	def doInsert(self, data):
		spc = data.find(' ')
		drive = data[:spc]
		path = data[spc+1:]
		#(drive, path) = data.split(' ')
		self.server.open(int(drive), path)
		return "open(%d, %s)" % (int(drive), path)
	def doEject(self, data):
		drive = data.split(' ')[0]
		self.server.close(int(drive))
		return "close(%d)" % (int(drive))
	def doInstance(self, data):
		out = ['','']
		out.append( "Inst.  Type" )
		out.append( "-----  --------------------------------------" )
		#i=0
		#for f in self.server.files:
		out.append( "%d      %s" % (0, self.server.conn.__class__))
		#	i += 1
		
		out.append('')
		return '\n\r'.join(out)
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
	#def doDir(self, data, nxti):
	def doDir(self, data):
		out = ['']
		cmd = ['ls']
		#if nxti != -1:
		#	path = data[nxti+1:].split(' ')[0]
		#	cmd.append(path)
		if not data:
			raise Exception("dir: Bad data")
		if data:
			cmd.append(data)
		print cmd
		data2 = subprocess.Popen(
			" ".join(cmd),
			stdout=subprocess.PIPE,
			stderr=subprocess.STDOUT,
			shell=True)	
		out.extend(data2.stdout.read().split('\n'))
		out.append('')
		return '\n\r'.join(out)

	def doList(self, path):
		out = []
		cmd = ['cat']
		#path = data.split(' ')[0]
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
		u = data.upper()
		if u.startswith("AT"):
			tokens=["AT"]
			t2 = u[2:]
			if t2:
				tokens.append(t2)
			else:
				return "OK"
		else:
			tokens = data.split(' ')
		p = self.parseTree
		i = 0
		for t in tokens:
			#print t
			v=p.lookup(t)
			#print v
			if v:
				i += len(t) + 1
			if isinstance(v, ParseNode):
				p = v
			elif isinstance(v, ParseAction):
				callData = data[i:]
				#print callData
				return v.call(callData)	
			else:
				break

		if t:
			print "%s: Invalid command: %s" % (p.name, t)
		return p.help()
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
				print "pyDriveWire> ",
				wdata = raw_input()
			except EOFError:
				print
				print "Bye!"
				break
			
			# basic stuff
			if wdata.find(chr(4)) == 0 or wdata.find("exit") == 0:
				# XXX Do some cleanup... how?
				print "Bye!"
				break
			
			try:
				print self.parser.parse(wdata)
			except:
				print "ERROR"
				traceback.print_exc()

		self.server.conn.close()
		i=0
		for f in self.server.files:
			if f:
				self.server.close(int(i))
			i += 1
		os._exit(0)
if __name__ == '__main__':
	r = DWRepl(None)
	r.rt.join()

#finally:
#	cleanup()
