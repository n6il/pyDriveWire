#!/usr/local/bin/python
import serial
from dwserial import DWSerial
from dwsocket import DWSocketServer
from dwserver import DWServer
from dwcommand import DWRepl
import traceback
import logging


if __name__ == '__main__':
	import sys

	logging.basicConfig(stream=sys.stdout, level=logging.INFO,
		format='%(asctime)s %(levelname)s %(module)s:%(lineno)s.%(funcName)s %(message)s')
	if len(sys.argv) < 3:
		print("Usage: %s <port> <speed> <file>" % (sys.argv[0]))
		print('')
		print('\t%s /dev/tty.usbserial-FTF4ZN9S 19200' % sys.argv[0])
		print('\t%s accept <port>' % sys.argv[0])
		print('')
		sys.exit(1)

	(port, speed) = sys.argv[1:3]
	files = sys.argv[3:]
	if port == "accept":
		conn = DWSocketServer(port=speed)
		#conn.accept()
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
#	try:
#		while True:
#			wdata = raw_input()
#			conn.write(wdata)
#			#print "main: Wrote %d bytes" % len(wdata)
#			rdata = conn.read(len(wdata))
#			#print "main: Read %d bytes" % len(rdata)
#			print rdata
#	finally:
#		cleanup()
