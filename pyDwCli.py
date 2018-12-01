import urllib
import re
import traceback
import sys

if len(sys.argv) < 2:
    print "Usage: pyDwCli <url>"
    exit(1)

url = sys.argv[1]

while True:
        try: 
                print "pyDriveWire>",
                wdata = raw_input()
        except EOFError:
                print
                print "Bye!"
                break
        
        # basic stuff
        if wdata.find(chr(4)) == 0 or wdata.lower() in ["exit", "quit"] :
                # XXX Do some cleanup... how?
                print "Bye!"
                break
        
        if wdata.lower() in ["help", "?"] :
            conn = urllib.urlopen(url + '/help.html')
            html = conn.read()
            try:
                foo
                print html2text.html2text(html)
            except:
                print html
            continue

        try:
                wdata = re.subn('.\b', '', wdata)[0]
                wdata = re.subn('.\x7f', '', wdata)[0]
                conn = urllib.urlopen(url, wdata)
                print conn.read()
        except Exception as ex:
                print "ERROR:: %s" % str(ex)
                traceback.print_exc()

