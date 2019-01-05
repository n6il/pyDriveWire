# Experimental Printing Support

pyDriveWire v0.3 includes experimental printing support.  The `-x printer` command line option enables it.  Currently this only suports printing text, and the out is rendered into a PDF.

_Prerequisites_

Printing support requires the reportlab module.  This module can be installed with pip:

    pypy -m pip install reportlab

_Use_

Most of the standard Nitros9 DriveWire builds have printing support built in.  Any program that uses the standard `/P` printing device will work just fine.  A simple example for testing:

    dir >/P

The console log will explain where the output PDF went:

    DWServer: Enabling experimental printing support
    Printing: opening print buffer: /var/folders/1y/cjrxv35d76bc54myg7hy7k1c0000gn/T/tmp2zG0Pb.txt
    Printing to: /var/folders/1y/cjrxv35d76bc54myg7hy7k1c0000gn/T/tmpWdKRQY.pdf
    Printing: closing print buffer: /var/folders/1y/cjrxv35d76bc54myg7hy7k1c0000gn/T/tmp2zG0Pb.txt
