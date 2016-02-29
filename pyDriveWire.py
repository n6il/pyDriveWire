#!/usr/local/bin/python
import serial
from dwserial import DWSerial
from dwserver import DWServer
from dwcommand import DWRepl
import traceback

if __name__ == '__main__':
	import sys

	if len(sys.argv) < 3:
		print("Usage: %s <port> <speed> <file>" % (sys.argv[0]))
		print('')
		print('\t%s /dev/tty.usbserial-FTF4ZN9S 19200' % sys.argv[0])
		print('')
		sys.exit(1)

	(_, port, speed, file) = sys.argv
	conn = DWSerial(port, speed)
	conn.connect()

	dws = DWServer(conn)
	dwr = DWRepl(dws)
	
	def cleanup():
		#print "main: Closing serial port."
		dws.close(drive)
		conn.close()
	import atexit
	atexit.register(cleanup)

	try:
		drive = 0
		dws.open(drive, file)
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
