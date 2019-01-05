# pyDriveWire Daemon Mode for Linux/macOS

{{TOC}}

When pyDriveWire is run on any Linux/Unix/macOs operating system it can be run in a daemon mode where the server in the background in a "daemon" mode.  When run in this mode there is no console repl and you must use either the Web UI or pyDwCli to control it.

Note: This mode is _not_ supported on Windows

# Configuring Daemon mode

Daemon mode can be enabled from either the config file or from the command line.  You do not need to specify both but you can.  Note that if you do specify both the config file parameters will override the command line ones.

## Daemon mode from a config file

Either put this in your `~/.pydrivewirerc` file, or invoke the server with `pyDriveWire -C <config_file>`

    option uiPort 6800
    option daemon True
    option daemonPidFile /tmp/pyDriveWire.pid
    option daemonLogFile /tmp/pyDriveWire.log
    [... additional options required ...]

## Command Line Options

    $ ./pyDriveWire -h
    usage: pyDriveWire.py [-U UIPORT] [-C CONFIG]
                          [--daemon] [--status] [--stop]
                          [--pid-file DAEMONPIDFILE] [--log-file DAEMONLOGFILE]
                          [FILE [FILE ...]]

    pyDriveWire Server v0.4

    positional arguments:
      FILE                  list of files

    optional arguments:
      -U UIPORT, --ui-port UIPORT
                            pyDriveWire UI Port
      -C CONFIG, --config CONFIG
                            Config File
      --daemon              Daemon Mode, No Repl
      --status              Daemon Status
      --stop                Daemon Status
      --pid-file DAEMONPIDFILE
                            Daemon Pid File
      --log-file DAEMONLOGFILE
                            Daemon Log File

## Starting daemon mode from the command line

The server can be invoked as follows from the command line:

    ./pyDriveWire \
            --ui-port 6800 \
            --daemon \
            --pid-file /tmp/pyDriveWire.pid \
            --log-file /tmp/pyDriveWire.log \
            [... additional required options ...]
            
This will start the server in `daemon` mode with a web UI listening on port `6800`.
    
## Checking server status

Example: Daemon mode is not running

    $ ./pyDriveWire --status
    pyDriveWire Server status:notRunning

Example: Deamon mode is running

    $ ./pyDriveWire --status
    pyDriveWire Server pid:1114 status:Running
  
  
## Stopping the server

    $ ./pyDriveWire --status
    pyDriveWire Server pid:1114 status:Running
    
    $ ./pyDriveWire --stop
    pyDriveWire Server pid:1114 msg:Stopped

    $ ./pyDriveWire --status
    pyDriveWire Server status:notRunning