#!/bin/bash -e

cat <<EOF
**********************************************
pyDriveWire v0.6 Installation Script for macOS
**********************************************

This script will install all prerequisite packages for running pyDriveWire.
After the prerequisites have been installed you will be instructed on how
to complete pyDriveWire installtion and testing.

Please press Return to continue or q to quit:
EOF
read a
if [ "X$a" != "X" ]; then
	exit
fi

cat <<EOF

*************************************
Checking pyDriveWire Prerequisites...
*************************************

EOF
     


# XCode Command Line Tools
echo -n "Checking for XCode Command Line Tools... "
vers="$(sw_vers -productVersion | awk -F. '{print $1"."$2}')"
if (( $(echo "$vers > 10.13" | bc -l) )); then
	[ ! -e  "/Library/Developer/CommandLineTools/usr/bin/git" ]
	r=$?
else
	[[ ! -e  "/Library/Developer/CommandLineTools/usr/bin/git" || ! -e "/usr/include/iconv.h" ]]
	r=$?
fi

if (( $r == 0 )); then
	echo "Please follow the prompts to install... "
	xcode-select --install
	r=1
	while (( $r == 1 )); do
		sleep 0.5
		pid=$(pgrep "Install Command Line Developer Tools")
		r=$?
	done
	echo -n "Pid: $pid..."
	r=0
	while (( $r == 0 )); do
		sleep 0.5
		pid=$(pgrep "Install Command Line Developer Tools")
		r=$?
	done
	echo "Done"
else
	echo "Found"
fi

# Verify Command Line Tools Install
if (( $(echo "$vers > 10.13" | bc -l) )); then
	[ ! -e  "/Library/Developer/CommandLineTools/usr/bin/git" ]
	r=$?
else
	[[ ! -e  "/Library/Developer/CommandLineTools/usr/bin/git" || ! -e "/usr/include/iconv.h" ]]
	r=$?
fi

if (( $r == 0 )); then
	echo "ERROR: XCode Command Line Tools not installed properly"
	exit 2
fi

# HomeBrew
echo -n "Checking for HomeBrew... "
if [ "$(uname -p)" = "arm" ]; then 
	brewPath="/opt/homebrew"
else
	brewPath="/usr/local/homebrew"
fi
if [ !  -x "${brewPath}/bin/brew" ]; then
	echo "Please follow the prompts to install... "
	/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
	r=$?
	if (( $r != 0 )); then
		echo "ERROR: HomeBrew Install did not succeed, RC: $r"
		exit $r
	fi
	echo "Done"
else
	echo "Found"
fi

# Verify HomeBrew Install
if [ !  -x "${brewPath}/bin/brew" ]; then
	echo "ERROR: HomeBrew not found at expected location: ${brewPath}/bin/brew"
	exit 2
fi

echo -n "Checking HomeBrew Environment... "
if [ -z "${HOMEBREW_PREFIX}" ]; then
	echo -n  "Setting up... "
	eval "$(${brewPath}/bin/brew shellenv)"
	echo "Done"
else
	echo "Found"
fi

# Home Brew Packages
s=()
for i in pyenv openssl@1.1 rust jpeg-turbo zlib; do
	echo -n "Checking for HomeBrew Package: $i... "
	brew ls --versions $i 2>/dev/null >/dev/null
	r=$?
	if (( $r == 1 )); then
		echo "Not installed"
		s+=($i)
	else
		echo "Found"
	fi
done

if (( ${#s[@]} > 0 )); then 
	echo -n "Installing HomeBrew Package(s): ${s[@]}..."
	brew install ${s[@]}
	r=$?
	if (( $r != 0 )); then
		echo "ERROR: HomeBrew Package Install did not succeed, RC: $r"
		exit $r
	fi
	echo "Done"
fi

# Verify HomeBrew Packages
e=1
for i in pyenv openssl@1.1 rust jpeg-turbo zlib; do
	brew ls --versions $i 2>/dev/null >/dev/null
	r=$?
	if (( $r == 1 )); then
		echo "ERROR: HomeBrew Package: $i: Not installed"
		e=0
	fi
done
if (( $e == 0 )); then
	exit 2
fi

if [ !  -x "${brewPath}/bin/pyenv" ]; then
	echo "ERROR: pyenv not found at expected location: ${brewPath}/bin/pyenv"
	exit 2
fi

     
cd ~

if [ "$(uname -p)" = "arm" ]; then 
	cat >/tmp/np <<'EOF'
# Set PATH, MANPATH, etc., for Homebrew.
eval "$(/opt/homebrew/bin/brew shellenv)"
EOF
else
	cat >/tmp/np <<'EOF'
# Set PATH, MANPATH, etc., for Homebrew.
eval "$(/usr/local/homebrew/bin/brew shellenv)"
EOF
fi
	cat >>/tmp/np <<'EOF'
# pyenv setup for pyDriveWire
export PYENV_ROOT="$HOME/.pyenv"
command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
EOF

s=1
for i in ~/.zprofile ~/.zshrc; do
	echo -n "Checking zsh environment file: $i... "
	if [ -e "${i}" ]; then
		fgrep -q -f /tmp/np $i
		r=$?
	else
		r=1
	fi
	if (( $r != 0 )); then
		echo -n "Installing... "
		cat /tmp/np >> $i
		s=0
		echo "Done"
	else
		echo "Found"
	fi
done
rm /tmp/np

echo -n "Checking pyenv environment... "
if [ -z "${PYENV_ROOT}" ]; then
	echo -n "Setting up... "
	# pyenv setup for pyDriveWire
	export PYENV_ROOT="$HOME/.pyenv"
	command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
	eval "$(pyenv init -)"
	echo "Done"
else
	echo "Found"
fi
    
cd ~
pyVersion="pypy2.7-7.3.11"
echo -n "Checking for Python version: $pyVersion... "
pyenv versions | grep -q  $pyVersion
r=$?
if (( $r != 0 )); then
	echo "Installing... "
	pyenv install $pyVersion
	echo "Done"
else
	echo "Found"
fi
pyenv shell $pyVersion
pyenv which python >/dev/null
r=$?
if (( $r != 0 )); then
	echo "ERROR: python not found!"
	exit 2
fi


echo "Checking for Python Modules. Python version: $pyVersion..."
echo -n "Checking for Python module: reportlab... "
python -m pip list --disable-pip-version-check --no-python-version-warning 2>/dev/null | grep -q reportlab
r=$?
if (( $r != 0 )); then
	echo "Installing... "
	LDFLAGS="-L$(brew --prefix zlib)/lib -L$(brew --prefix jpeg-turbo)/lib"
	CFLAGS="-I$(brew --prefix zlib)/include -I$(brew --prefix jpeg-turbo)/include"
	env "LDFLAGS=${LDFLAGS}" "CFLAGS=${CFLAGS}" python -m pip install --disable-pip-version-check --no-python-version-warning reportlab
	r=$?
	if (( $r != 0 )); then
		echo "ERROR: Problem installing reportlab RC: $r"
		exit $r
	fi
	echo "Done"
else
	echo "Found"
fi

for i in ecdsa paramiko; do
	echo -n "Checking for Python module: $i... "
	python -m pip list --disable-pip-version-check --no-python-version-warning 2>/dev/null | grep -q $i
	r=$?
	if (( $r != 0 )); then
		echo "Installing... "
		LDFLAGS="-L$(brew --prefix openssl@1.1)/lib"
		CFLAGS="-I$(brew --prefix openssl@1.1)/include"
		env "LDFLAGS=${LDFLAGS}" "CFLAGS=${CFLAGS}" python -m pip install --disable-pip-version-check --no-python-version-warning $i
		r=$?
		if (( $r != 0 )); then
			echo "ERROR: Problem installing: $i RC: $r"
			exit $r
		fi
		echo "Done"
	else
		echo "Found"
	fi
done

for i in serial playsound; do
	echo -n "Checking for Python module: $i... "
	python -m pip list --disable-pip-version-check --no-python-version-warning 2>/dev/null | grep -q $i
	r=$?
	if (( $r != 0 )); then
		echo "Installing... "
		python -m pip install --disable-pip-version-check --no-python-version-warning $i
		r=$?
		if (( $r != 0 )); then
			echo "ERROR: Problem installing: $i RC: $r"
			exit $r
		fi
		echo "Done"
	else
		echo "Found"
	fi
done

cat <<EOF

***************************************
Installation  of Prerequisites Complete
***************************************

EOF
     
dir="${HOME}/src/pyDriveWire"
if [ ! -d "${dir}" ];  then
	i="foo"
        while [ "X${i}" != "X" ]; do
                echo "pyDriveWire will be installed to: ${dir}"
                echo -n  "Press Return to accept or type another path: "
                read i
		echo
                if [ "X${i}" != "X" ]; then
                        dir="${i}"
                fi
	done
	if [[ "${dir}" = *"pyDriveWire" ]]; then
		dd=$(dirname "${dir}")
	else
		dd="${dir}"
		dir="${dd}/pyDriveWire"
	fi
	if [ -d "${dir}" ]; then
		echo "pyDriveWire already installed at: ${dir}"
		if [ ! -e "${dir}/.python-version" ]; then
			echo "Setting pyDriveWire Python version to: $pyVersion..."
			( cd "${dir}"; pyenv local $pyVersion ) & wait
		fi
	else
		set -x
		mkdir -p "${dd}"
		cd "${dd}"
		git clone https://github.com/n6il/pyDriveWire.git
		cd pyDriveWire
		pyenv local $pyVersion
		set +x
	fi
	echo

	cat <<EOF
******************************************************************************
pyDriveWire has been installed to: ${dir}
You can test the pyDriveWire installtion by performing the following steps:
******************************************************************************

EOF
else
	if [ ! -e "${dir}/.python-version" ]; then
		echo "Setting pyDriveWire Python version to: $pyVersion..."
		( cd "${dir}"; pyenv local $pyVersion ) & wait
	fi
	cat <<EOF
******************************************************************************
pyDriveWire already installed at: ${dir}
You can test the pyDriveWire installtion by performing the following steps:
******************************************************************************

EOF
fi

cat <<EOF
cd ${dir}
./pyDriveWire -x ssh -x playsound -x printer --accept --port 65504 --ui-port 6800

At the "pyDriveWire> prompt type "exit"

******************************************************************************
Please see the manual for additional information on using pyDriveWire.
******************************************************************************

EOF
