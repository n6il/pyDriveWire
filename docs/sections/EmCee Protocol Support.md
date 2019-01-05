# Experimental EmCee Protocol Support
pyDriveWire version v0.4 adds experimental support for the EmCee protocol used on the TRS-80 MC-10 running MCX Basic (MCX Basic is available on the MCX-128 expansion card).  The EmCee protocol support is always turned on allowing any application connected to a pyDriveWire server to use EmCee and DriveWire protocols simultaneously.  With this setup one could use a DriveWire application on a MC-10 or a EmCee application on a CoCo without the need to switch servers.

As of v0.4 the following MCX Basic Commands are supported:

* `SETDIR`
* `DIR`
* `LOAD`
* `LOADM`


The following file formats are supported:

* `.C10`
* `.CAS`


## Important Note about Simultaneous use of DriveWire and EmCee Protocols
Drive 0 will be used by the EmCee server for mounting the `.C10` or `.CAS` files.  Any DriveWire disk in Drive 0 will be unmounted. If data was written to the DriveWire disk in Drive 0 it is highly recommended to umount the DriveWire disk using the `dw disk eject 0` command before using any of the EmCee features. 

## Notes

1. You must use 38400 baud to use the EmCee protocol on  a MC-10 running MCX Basic
2. The `SETDIR` command works differently than the standard EmCee Server.
3. At the current time pyDriveWire _only_ supports `.C10` and `.CAS` formatted files.  WAV and BIN file support is planned for a future update.
4. At the current time you cannot open a `.C10` or `.CAS` file from the command line.  Use the `LOAD`,  `LOADM`  or `OPEN` commands.

## Using pyDriveWire's EmCee Server

The EmCee server in pyDriveWire is on by default and there are no commands to turn it on or off.  The only special requirement is that ***You must use 38400 baud to use the EmCee protocol on  a MC-10 running MCX Basic***.  Please see the rest of this documentation for how to invoke pyDriveWire.  Once pyDriveWire is started you can use the normal MCX Basic commands to access files on the server.

## `SETDIR <path>` - Set the directory on the server

#### Options

* `<path>` --  full path name a directory on the server

#### Description 

The pyDriveWire version of `SETDIR` is different than the normal EmCee server.  You must provide a full path name to the directory you want to switch to.

#### Examples

* Windows: `SETDIR C:\Users\Mikey\MC-10`
* Mac/Linux: `SETDIR /home/Mikey/MC-10`


## `DIR [<path>]` - List directory on the server

#### Options

* `<path>` --  optional full path name a directory on the server

#### Description

List the directory on the server.  The default directory is the one where pyDrivewire was invoked. `<path>` is optional and must be a full path name to the directory you want to list.

#### Examples

* `DIR`
* Windows: `DIR C:\Users\Mikey\MC-10`
* Mac/Linux: `DIR /home/Mikey/MC-10`

