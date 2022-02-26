pyinstaller -p /usr/local/lib/python2.7/site-packages --hidden-import reportlab --hidden-import pillow --hidden-import paramiko  --hidden-import playsound --add-data ui:ui --add-data fonts:fonts -F pyDriveWire.py

