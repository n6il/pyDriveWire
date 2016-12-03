#!/usr/local/bin/python
import serial
from dwserial import DWSerial
from dwsocket import DWSocketServer, DWSocket
from dwserver import DWServer
from dwcommand import DWRepl
import traceback
import logging


if __name__ == '__main__':
	import sys

	logging.basicConfig(stream=sys.stdout, level=logging.INFO,
		format='%(asctime)s %(levelname)s %(module)s:%(lineno)s.%(funcName)s %(message)s')
	if len(sys.argv) < 3:
		print("Usage: %s <port> <speed> [<file>] [...]" % (sys.argv[0]))
		print('')
		print('\t%s /dev/tty.usbserial-FTF4ZN9S 115200 ...' % sys.argv[0])
		print('\t%s accept <port> ...' % sys.argv[0])
		print('\t%s connect <host> <port> ...' % sys.argv[0])
		print('')
		sys.exit(1)

	(port, speed) = sys.argv[1:3]
	files = sys.argv[3:]
	print port, speed, files
	if port == "accept":
		conn = DWSocketServer(port=speed)
		#conn.accept()
	elif port == "connect":
		(host, port) = sys.argv[2:4]
		files = sys.argv[4:]
		print "host",host,"port",port,"files",files
		conn = DWSocket(port=port,host=host)
		conn.connect()
		conn.run()
		#exit(0)
	else:
		conn = DWSerial(port, speed)
		conn.connect()

	def cleanup():
		#print "main: Closing serial port."
		dws.close(drive)
		conn.cleanup()
	import atexit
	atexit.register(cleanup)
	print conn.__class__

	dws = DWServer(conn)
	dwr = DWRepl(dws)

	try:
		drive = 0
		for f in files:
			dws.open(drive, f)
			drive += 1
		dws.main()
	except:
		traceback.print_exc()
	finally:
		cleanup()

