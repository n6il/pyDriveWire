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
from argparse import Namespace

import sys
import os
import time
import threading
import atexit

from daemon import Daemon
import platform

VERSION = 'v0.5pre'

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
    parser.add_argument('--daemon', dest='daemon', action='store_true', help='Daemon Mode, No Repl')
    parser.add_argument('--status', dest='daemonStatus', action='store_true', help='Daemon Status')
    parser.add_argument('--stop', dest='daemonStop', action='store_true', help='Daemon Status')
    parser.add_argument('--pid-file', dest='daemonPidFile', help='Daemon Pid File')
    parser.add_argument('--log-file', dest='daemonLogFile', help='Daemon Log File')

    parser.add_argument('files', metavar='FILE', nargs='*',
                    help='list of files')

    args = parser.parse_args()

    args = ReadConfig(args)

    err = None
    if not any([args.port, args.accept, args.connect, args.daemon, args.daemonStatus, args.daemonStop]):
        err = "Must supply one of --port, --accept, or --connect or config file"
    elif args.accept and not args.port:
        err = "TCP Accept must supply --accept and --port"
    elif args.connect and not all([args.port,args.host]):
        err = "TCP Connect must supply --connect, --host, and --port"
    elif not args.accept and not args.connect and not all([args.speed, args.port]):
        err = "Serial connection must supply --speed and --port"
    elif args.daemon and platform.system() in ['Windows']:
        err = "Daemon mode not supported on %s" % platform.system()
    elif args.daemon and not args.uiPort and not args.cmdPort:
        err = "Daemon mode must have a user interface port, --ui-port"
    elif args.daemon and (not args.daemonPidFile or not args.daemonLogFile):
        err = "Daemon mode must specify --pid-file and --log-file"
    elif args.daemonStop and not args.daemonPidFile:
        err = "Daemon stop: Must specify --pid-file"
    elif args.daemonStatus and not args.daemonPidFile:
        err = "Daemon status:  Must specify --pid-file"

    if err:
        print(err)
        parser.print_usage()
        exit(1)

    return args

def ReadConfig(args):
    instances = []
    args.cmds = []

    i = 0
    instance = 0
    iargs = args

    cfgFile = os.path.expanduser(args.config)
    if not os.path.exists(cfgFile):
        return args
    with open(cfgFile) as f:
        for l in f:
            l = l.lstrip().rstrip()
            if l.startswith('#') or l=='':
                continue
            if l.startswith('['):
                instName = l[1:-1]
                instance += 1
                iargs = Namespace()
                iargs.accept = False
                iargs.connect = False
                iargs.host = None
                iargs.port = None
                iargs.speed = None
                iargs.experimental = []
                iargs.daemon = True
                iargs.rtscts = False
                iargs.files = []
                iargs.cmds = []
                instances.append(iargs)
                continue
            lp = l.split(' ')
            if lp[0].lower() == 'option':
                #args[lp[1]] = lp[2]
                val = lp[2]
                if val in ['True', 'False']:
                        val = eval(val)
                exec('iargs.%s = val' % lp[1])
                #print "%d:option:%s" % (instance,l)
            else:
                iargs.cmds += [l]
                #print "%d:cmd:%s" % (instance,l)
    args.instances = instances
    #args.cmds = cmds
    return args


def CreateServer(args, instance, instances, lock):
	if args.accept:
                print("Accept connection on %s" % args.port)
		conn = DWSocketServer(port=args.port)
	elif args.connect:
                print "Connect to %s:%s" % (args.host,args.port)
		conn = DWSocket(port=args.port,host=args.host)
		conn.connect()
		conn.run()
	else:
                print "Serial Port: %s at %s, RTS/CTS=%s" % (args.port, args.speed, args.rtscts)
		conn = DWSerial(args.port, args.speed, rtscts=args.rtscts)
		conn.connect()

	dws = DWServer(args, conn, VERSION, instances, instance)
        lock.acquire()
        instances[instance] = dws
        lock.release()


        parser = DWParser(dws)
        for cmd in args.cmds:
            print instance,cmd
            parser.parse(cmd)

        return dws

def StartServer(args, dws):
	def cleanup():
		#print "main: Closing serial port."
                for server in dws.instances:
                    server.closeAll()
                    server.conn.cleanup()

        if dws.instance == 0:
            atexit.register(cleanup)

	try:
		drive = 0
		for f in args.files:
			dws.open(drive, f)
			drive += 1
                if dws.instance == 0:
                    if args.cmdPort:
                            dwe = DWRemoteRepl(dws, args.cmdPort)
                    if args.uiPort:
                            dwhts = DWHttpServer(dws, int(args.uiPort))
                    if not args.daemon:
                        dwr = DWRepl(dws)
		dws.main()
	except:
		traceback.print_exc()
	finally:
		cleanup()


instances = [None]
lock = threading.Lock()
def StartServers(args):
    global instances
    global lock
    instances = [None] * (len(args.instances) + 1)
    threads = []
    #lock = threading.Lock()
    j = 1
    for iargs in args.instances:
        dws = CreateServer(iargs, j, instances, lock)
        instances[j] = dws
        t = threading.Thread(target = StartServer, args=([iargs, dws]))
        t.daemon = True
        threads.append(t)
        j += 1

    dws = CreateServer(args, 0, instances, lock)
    instances[0] = dws

    for i in range(len(instances)):
        instances[i].instances = instances
        instances[i].instance = i

    for t in threads:
        t.start()
    StartServer(args, dws)

class pyDriveWireDaemon(Daemon):
        def run(self):
            StartServers(self.args)

if __name__ == '__main__':
#	logging.basicConfig(stream=sys.stdout, level=logging.INFO,
#		format='%(asctime)s %(levelname)s %(module)s:%(lineno)s.%(funcName)s %(message)s'

    args = ParseArgs()
    daemon = None
    pid = None
    status = 'notRunning'
    if args.daemon or args.daemonStatus or args.daemonStop:
        pidFile = args.daemonPidFile
        daemon = pyDriveWireDaemon(pidFile, args, stdout=args.daemonLogFile, stderr=args.daemonLogFile)
        if args.daemonStatus or args.daemonStop:
            pid = daemon.getPid()
            if pid:
                status = daemon.getStatus()
    if args.daemonStatus:
            pidMsg = '\b'
            if pid:
                pidMsg  = 'pid:%d' % pid
            print "pyDriveWire Server %s status:%s" % (pidMsg, status)
    elif args.daemonStop:
        msg = ''
        if status == 'Running':
            daemon.stop()
            msg = 'Stopped'
        else:
            msg = status
        print "pyDriveWire Server pid:%s msg:%s" % (pid, msg)
    elif args.daemon:
        daemon.start()
        pid = daemon.getPid()
        status = daemon.getStatus()
        print "pyDriveWire Server %s status:%s" % (pidMsg, status)
        sys.path.stdout.flush()
        sys.exit(0)
    else:
        StartServers(args)
