~/.local/bin/pyinstaller -p /usr/local/lib/python2.7/site-packages -p /home/pi/.local/lib/python2.7/site-packages --hidden-import reportlab --hidden-import pillow --hidden-import paramiko --hidden-import playsound --add-data ui:ui --add-data fonts:fonts -F pyDriveWire.py
~/.local/bin/pyinstaller -p /usr/local/lib/python2.7/site-packages -p /home/pi/.local/lib/python2.7/site-packages -F pyDwCli.py
