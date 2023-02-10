# pyDriveWire General Installation Instructions

v0.6 2023-02-09 23:18

### Introduction

pyDriveWire is a Python 2 project at the current time.  Since Python 2 reached End Of Life in April 2020, it has become increasingly more difficult to install Python 2 and the associated packages.  We recommend using `pyenv` to install and manage the recommended version of Python (pypy2.7-7.3.11).  This document provides both quickstart and step-by-step instructions for installing `pyenv` and pyDriveWire. 

The latest version of this document will always be at: [https://github.com/n6il/pyDriveWire/tree/master/docs/pyDriveWire%20General%20Installation%20Instructions.md](https://github.com/n6il/pyDriveWire/tree/master/docs/pyDriveWire%20General%20Installation%20Instructions.md)

### <a name="toc">Table of Contents<toc></a>

1. [Quickstart Guide](#quickstart)
2. [Step-by-step Instructions](#steps)

## <a name="quickstart">Quickstart Guide</a>


### Ready-to-go Binaries for Linux/Windows/RPi

Binary packages are available at the following location:

[https://github.com/n6il/pyDriveWire/releases/latest](https://github.com/n6il/pyDriveWire/releases/latest)

Packages are available for the following operating systems:

* `linux-x86_64` -- Any modern 64-bit Linux 
* `win-x64` -- 64-bit Windows (Windows 7 or later)
*  `rpi` -- Raspberry Pi 3/4 (Raspbian Jesse)

### General DIY/Self Install Instructions

1. Install `pyenv`
2. `pyenv install pypy2.7-7.3.11`
3. `cd ~/src/pyDriveWire`
4. `pyenv version pypy2.7-7.3.11`
5. `pypy -m pip install serial ecdsa paramiko reportlab playsound`


[Return to toc](#toc)

### macOS
Open a Terminal and run the following command to perform an automated installation of pyDriveWire v0.6 on your Mac:

```
/bin/bash -c "$(curl -fsSL https://github.com/n6il/pyDriveWire/releases/download/v0.6/installer-macOS.sh)"
```

## <a name="steps">Step-by-step instructions</a>
### 1. Install pyenv

Use your package manager.  If it's not available you can run:

    curl https://pyenv.run | bash

### 2. Set up Environment for Python

This step sets up the `bash` shell to run Python with `pyenv`:

    cd ~
    
    cat >/tmp/np <<EOF
    # pyenv setup for pyDriveWire
    export PYENV_ROOT="$HOME/.pyenv"
    command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
    eval "$(pyenv init -)"
    EOF
     
    cat /tmp/np >> ~/.profile
    cat /tmp/np >> ~/.bashrc
    source /tmp/np
     
    rm /tmp/np

### 3. Install Pypy 2.7

Install the recommended version of python:

    pyenv install pypy2.7-7.3.11
     
### 4. Install Python Libraries and Packages

Run the following commands one at a time and ensure that each one succeeds.  There will be some red text on the screen if there is any error.

    pyenv shell pypy2.7-7.3.11 
    pypy -m pip install serial ecdsa paramiko reportlab 
    playsound 

### 5. Obtain pyDriveWire Code

    mkdir ~/src
    cd ~/src
    git clone https://github.com/n6il/pyDriveWire.git

### 6. Set pyDriveWire Python Version

    cd ~/src/pyDriveWire
    pyenv local pypy2.7-7.3.11
 
### 7. pyDriveWire Test Run

This command is a simple test run of pyDriveWire.  Please refer to the full [pyDriveWire Manual](https://github.com/n6il/pyDriveWire/blob/master/docs/The%20pyDriveWire%20Manual.md) for further information on running and configuring pyDriveWire.

    cd ~/src/pyDriveWire
    ./pyDriveWire --accept --port 65504 --ui-port 6800 -x printer -x ssh
    
 After running this you should see the following on your screen:
 
    % ./pyDriveWire --accept --port 65504 --ui-port 6800 -x printer -x ssh
    Accept connection on 65504
    DWServer: Enabling experimental printing support
    DWServer: Enabling experimental ssh support
    Web UI running at http://localhost:6800
    
    ****************************************
    * pyDriveWire Server v0.6
    *
    * Enter commands at the prompt
    ****************************************
    
    pyDriveWire>   
    
 Type `exit` at the prompt:
 
    pyDriveWire>  exit
    Bye!
    %

[Return to toc](#toc)