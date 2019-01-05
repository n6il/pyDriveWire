# EmCee Server Aliases
The pyDriveWire server has a powerful "aliasing" system that is quite different than the official EmCee servers.  The pyDriveWire system has three different types of aliases.  File and Web Aliases can be  with LOAD/SAVE commands and Path Aliases can be used with DIR/SETDIR commands.  The official servers can only use aliases for the `SETDIR` command.

## Aliases are _NOT_ case sensitive
In the pyDriveWire server all alias names are converted to upper case.  For example if you had an alias like this one:

    Server Aliases
    ==============
    Alias: DWTERM.WAV Path: /demo/dwterm.wav

The case of the alias requested from the MC-10 is always converted to upper case so any of the following would load the same alias:

* `LOADM "DWTERM.WAV"`
* `LOADM "dwterm.wav"`
* `LOADM "DwTeRm.WaV"`

## Types of aliases

The PyDriveWire Server supports the following types of Aliases:

* Web Aliases
* Path Aliases
* File Aliases

A _web alias_ is an alias to a HTTP URL.  When the MC-10 requests the alias using a `LOAD` or `LOADM` command the URL which the alias points to will be downloaded to a temporary file and then opened normally.  Note that you won't see the actual file name, and when the file is closed the temp file will be automatically deleted.

A _path alias_ is an alias to a directory.  Path aliases can be used with `DIR` or `SETDIR` commands to change to the directory pointed to by the alias.

A _file alias_ points to a file.  Full or relative pathnames could be used.  When the MC-10 requests the the alias the path to which the alias points to will be used and opened normally.

See the help for `mc alias show` for an example.

## `mc alias show`
Show the currently installed aliases:

    Server Aliases
    ==============
    Alias: POKER.C10 Path: http://www.colorcomputerarchive.com/coco/MC-10/Cassettes/Games/Jim%20Gerrie's%20Games/POKER.C10
    Alias: DEMO Path: /demo
    Alias: DWTERM.WAV Path: /demo/dwterm.wav

Explanation of example Aliases:

* `POKER.C10` -- This is a _web alias_ -- `LOAD "POKER.C10"`
* `DEMO` -- This alias is a _directory alias_ -- `SETDIR "DEMO"`
* `DWTERM.WAV` -- This is a _file alias_ -- `LOADM "DWTERM.WAV"`

## `mc alias add <alias> <path>`

Adds the requested alias with path as the destination. The alias is always converted to upper case before addition lookup. The path that an alias points to is case sensitive.  Spaces and punctuation are permitted.

Add a Web Alias:

    pyDriveWire>  mc alias add poker.c10 http://www.colorcomputerarchive.com/coco/MC-10/Cassettes/Games/Jim%20Gerrie's%20Games/POKER.C10
    Add Alias
    ==============
    Alias: POKER.C10 Path: http://www.colorcomputerarchive.com/coco/MC-10/Cassettes/Games/Jim%20Gerrie's%20Games/POKER.C10

Add a file alias:

    pyDriveWire>  mc alias add dwterm.wav /demo/dwterm.wav
    Add Alias
    ==============
    Alias: DWTERM.WAV Path: /demo/dwterm.wav

## `mc alias remove <alias>`

Remove an alias.  The alias is always converted to upper case before addition removal.

    pyDriveWire>  mc alias remove qbert.c10
    Remove Alias
    ==============
    Alias: QBERT.C10 Path: http://www.colorcomputerarchive.com/coco/MC-10/Cassettes/Games/Jim%20Gerrie's%20Games/QBERT.C10
