# pyDriveWire Installation Instructions for macOS

v0.6 2023-02-09 23:18

### Introduction

pyDriveWire is a Python 2 project at the current time.  Since Python 2 reached End Of Life in April 2020, it has become increasingly difficult to install Python 2 and the associated packages.  We recommend using `pyenv` to install and manage the recommended version of Python (pypy2.7-7.3.11).  This document provides both quickstart and step-by-step instructions for installing `pyenv` and pyDriveWire. 

### <a name="toc">Table of Contents<toc></a>

1. [Quickstart Guide](#quickstart)
2. [Step-by-step Instructions](#steps)

## <a name="quickstart">Quickstart Guide</a>

Open a Terminal and run the following command to perform an automated installation of pyDriveWire v0.6 on your Mac:

```
/bin/bash -c "$(curl -fsSL https://github.com/n6il/pyDriveWire/releases/download/v0.6/installer-macOS.sh)"
```

[Return to toc](#toc)

## <a name="steps">Step-by-step instructions</a>
### 1. Install XCode Command Line Tools

XCode Command Line Tools contain all of the necessary compilers, libraries, and scripts required to perform the rest of the installation steps.  Note that this a separate install from the full XCode program from the AppStore.

    xcode-select --install
     
### 2. Install [HomeBrew](https://brew.sh)

[HomeBrew](https://brew.sh) is a package manager which allows you to install a wide variety of open source software on your Mac.  [HomeBrew](https://brew.sh) is installed with the following command: 

    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

### 3. Install Required System Libraries and Packages

Use [HomeBrew](https://brew.sh) to install system libraries and packages required for Python and pyDriveWire:

    brew install pyenv openssl@1.1 rust jpeg-turbo zlib

### 4. Set up Environment for HomeBrew and Python

This step sets up the `zsh` shell to make it easier to run HomeBrew and Python utilities.

    cd ~
    
    cat >/tmp/np <<EOF
    # Set PATH, MANPATH, etc., for Homebrew.
    eval "$(/opt/homebrew/bin/brew shellenv)"
    # pyenv setup for pyDriveWire
    export PYENV_ROOT="$HOME/.pyenv"
    command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
    eval "$(pyenv init -)"
    EOF
     
    cat /tmp/np >> ~/.zprofile
    cat /tmp/np >> ~/.zshrc
    source /tmp/np
     
    rm /tmp/np

### 5. Install Pypy 2.7

Install the recommended version of python.

    pyenv install pypy2.7-7.3.11
     
### 6. Install Python Libraries and Packages

Run the following commands one at a time and ensure that each one succeeds.  There will be some red text on the screen if there is any error.

    LDFLAGS="-L$(brew --prefix zlib)/lib -L$(brew --prefix jpeg-turbo)/lib"
    CFLAGS="-I$(brew --prefix zlib)/include -I$(brew --prefix jpeg-turbo)/include"
    env "LDFLAGS=${LDFLAGS}" "CFLAGS=${CFLAGS}" python -m pip install reportlab
    
    LDFLAGS="-L$(brew --prefix openssl@1.1)/lib"
    CFLAGS="-I$(brew --prefix openssl@1.1)/include"
    env "LDFLAGS=${LDFLAGS}" "CFLAGS=${CFLAGS}" python -m pip install ecdsa paramiko   
    
    python -m pip install serial playsound 


### 7. Obtain pyDriveWire Code

    mkdir ~/src
    cd ~/src
    git clone https://github.com/n6il/pyDriveWire.git
     
### 8. pyDriveWire Test Run

This command is a simple test run of pyDriveWire.  Please refer to the full [pyDriveWire Manual](https://github.com/n6il/pyDriveWire/blob/master/docs/The%20pyDriveWire%20Manual.md) for further information on running and configuring pyDriveWire.

    cd ~/src/pyDriveWire
    pyenv local pypy2.7-7.3.11
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