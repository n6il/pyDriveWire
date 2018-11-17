#!/usr/local/bin/python
import serial
from dwserial import DWSerial
from dwsocket import DWSocketServer, DWSocket
from dwserver import DWServer
from dwcommand import DWRepl, DWRemoteRepl, DWParser
from dwhttpserver import DWHttpServer
import traceback
import logging
import argparse

import sys
import os

VERSION = 'v0.4'

def ParseArgs():
    parser = argparse.ArgumentParser(description='pyDriveWire Server %s' % VERSION)
    parser.add_argument('-s', '--speed', dest='speed', help='Serial port speed')
    parser.add_argument('-a', '--accept', dest='accept', action='store_true', help='Accept incoming TCP connections on --port')
    parser.add_argument('-c', '--connect', dest='connect', action='store_true', help='Connect to TCP connections --host --port')
    parser.add_argument('-H', '--host', dest='host', help='Hostname/IP')
    parser.add_argument('-p', '--port', dest='port', help='Port to use')
    parser.add_argument('-R', '--rtscts', dest='rtscts', action='store_true', help='Serial: Enable RTS/CTS Flow Control')
    parser.add_argument('-x', dest='experimental', action='append', help='experimental options')
    parser.add_argument('-D', '--cmd-port', dest='cmdPort', help='Remote dw command input')
    parser.add_argument('-U', '--ui-port', dest='uiPort', help='pyDriveWire UI Port')
    parser.add_argument('-C', '--config', dest='config', help='Config File', default="~/.pydrivewirerc")
    parser.add_argument('files', metavar='FILE', nargs='*',
                    help='list of files')

    args = parser.parse_args()

    args = ReadConfig(args)

    err = None
    if not any([args.port, args.accept, args.connect]):
        err = "Must supply one of --port, --accept, or --connect or config file"
    elif args.accept and not args.port:
        err = "TCP Accept must supply --accept and --port"
    elif args.connect and not all([args.port,args.host]):
        err = "TCP Connect must supply --connect, --host, and --port"
    elif not args.accept and not args.connect and not all([args.speed, args.port]):
        err = "Serial connection must supply --speed and --port"

    if err:
        print(err)
        parser.print_usage()
        exit(1)

    return args

def ReadConfig(args):
    cmds = []
    args.cmds = cmds

    i = 0
    cfgFile = os.path.expanduser(args.config)
    if not os.path.exists(cfgFile):
        return args
    with open(cfgFile) as f:
        for l in f:
            l = l.lstrip().rstrip()
            if l.startswith('#') or l=='':
                continue
            lp = l.split(' ')
            if lp[0].lower() == 'option':
                #args[lp[1]] = lp[2]
                val = lp[2]
                if val in ['True', 'False']:
                        val = eval(val)
                exec('args.%s = val' % lp[1])
            else:
                cmds += [l]
    args.cmds = cmds
    return args

if __name__ == '__main__':
	import sys

        args = ParseArgs()
        #print(args)
	logging.basicConfig(stream=sys.stdout, level=logging.INFO,
		format='%(asctime)s %(levelname)s %(module)s:%(lineno)s.%(funcName)s %(message)s')
	#if len(sys.argv) < 3:
	#	print("Usage: %s <port> <speed> [<file>] [...]" % (sys.argv[0]))
	#	print('')
	#	print('\t%s /dev/tty.usbserial-FTF4ZN9S 115200 ...' % sys.argv[0])
	#	print('\t%s accept <port> ...' % sys.argv[0])
	#	print('\t%s connect <host> <port> ...' % sys.argv[0])
	#	print('')
	#	sys.exit(1)

	#(port, speed) = sys.argv[1:3]
	#files = sys.argv[3:]
	#print port, speed, files

	if args.accept:
                print("Accept connection on %s" % args.port)
		conn = DWSocketServer(port=args.port)
		#conn.accept()
	elif args.connect:
		#(host, port) = sys.argv[2:4]
		#files = sys.argv[4:]
		#print "host",host,"port",port,"files",files
                print "Connect to %s:%s" % (args.host,args.port)
		conn = DWSocket(port=args.port,host=args.host)
		conn.connect()
		conn.run()
		#exit(0)
	else:
                print "Serial Port: %s at %s, RTS/CTS=%s" % (args.port, args.speed, args.rtscts)
		conn = DWSerial(args.port, args.speed, rtscts=args.rtscts)
		conn.connect()

	def cleanup():
		#print "main: Closing serial port."
		dws.close(drive)
		conn.cleanup()
	import atexit
	atexit.register(cleanup)
	#print conn.__class__

	dws = DWServer(args, conn, VERSION)


        parser = DWParser(dws)
        for cmd in args.cmds:
            print cmd
            parser.parse(cmd)


	try:
		drive = 0
		for f in args.files:
			dws.open(drive, f)
			drive += 1
		if args.cmdPort:
			dwe = DWRemoteRepl(dws, args.cmdPort)
		if args.uiPort:
			dwhts = DWHttpServer(dws, int(args.uiPort))
		dwr = DWRepl(dws)
		dws.main()
	except:
		traceback.print_exc()
	finally:
		cleanup()

