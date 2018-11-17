# Windows Installation of PyPy(Python) and pyDriveWire

There are multiple ways to get Python and pyDriveWire installed on Windows.
As long as the basic requirements are met you can use any method to install
PyPy or Python.  The requirements and two fully-tested example installation
workflows are below.

# Requirements

* pyDriveWire is a Python 2.7 script.  It may or may not run on Python3
  (will likely migrate at a later time). 
* PyPy is preferred over CPython.  Pypy has Just-In-Time compilation and
  pyDriveWire will run a lot faster (and likely will also use lower CPU)
than CPython, but pyDriveWire is completely compatible with either one.
* Use the latest version of  _Python 2.7 Compatible PyPy for Windows_ or
  Python 2.7.X
* PyPy or Python should be installed in the system PATH
* PIP is required for installing required python modules
* PySerial module (use pip to install)
* Experimental Printing Support requires the ReportLab module (use pip to
  install)

# Bleeding Edge/Experimental/Pre-Release Features

The instructions below direct you to install the latest _stable release_
from the GitHub releases page.  If you would like to try out or help to
test the latest pyDriveWire code you can obtain pyDriveWire from it's
`develop` branch.  You can download a static zip file from GitHub or clone
the repository and switch to the `develop` branch.

We're more than happy to accept merge requests or bug reports for any
version you are trying.

# pyDriveWire Windows Installation Instructions (pypy)

1. Obtain the latest copy of _Python 2.7 Compatible PyPy for Windows_  from
   https://www.pypy.org/download.html
2. Extract it to the `C:\Program Files (x86)` folder
3. Add 2 entries to your system path:   
  a. the folder where you extracted PyPy to  
  b. the folder above and add `\bin` to the end
4. Download pip: https://bootstrap.pypa.io/get-pip.py
5. Install Pip. Open a command prompt and type: `pypy get-pip.py`
6. Install pyserial: `pip install pyserial`
7. Download (or git clone) the latest pyDriveWire release package from
   https://github.com/n6il/pyDriveWire/releases and extract it.
8. Versions 0.4 and later have a `pyDriveWire.bat` batch file you can run.
   Earlier versions can be started from the command prompt: `pypy
pyDriveWire.py <options>`

# pyDriveWire Windows Installation Instructions (msys2/CPython)

1. Obtain the latest version of the Mame MSYS2 development package from:
   https://www.mamedev.org/tools/
2. Extract it in `C:\` so the path is either `C:\msys64` or `C:\msys32`
3. Launch the `mingw64` shell
4. Download pip. In the mingw64 shell type: `wget https://bootstrap.pypa.io/get-pip.py`
5. Install Pip: `python get-pip.py`
6. Install pyserial: `pip install pyserial`
7. Download (or git clone) the latest pyDriveWire release package from
   https://github.com/n6il/pyDriveWire/releases and extract it.
8. From the mingw64 shell you can invoke pyDriveWire using the shell script: `./pyDriveWire <options>`


