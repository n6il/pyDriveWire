import urllib.request
import re
import traceback
import sys

if len(sys.argv) < 2:
    print("Usage: pyDwCli <url> [<cmd>]")
    sys.exit(1)

url = sys.argv[1]
cmd = None
if len(sys.argv) > 2:
    cmd = " ".join(sys.argv[2:])

while True:
    try:
        if cmd:
            wdata = cmd
        else:
            print("pyDriveWire>", end=" ")
            wdata = input()
    except EOFError:
        print()
        print("Bye!")
        break

    # basic stuff
    if wdata.find(chr(4)) == 0 or wdata.lower() in ["exit", "quit"]:
        # XXX Do some cleanup... how?
        print("Bye!")
        break

    try:
        wdata = re.subn('.\b', '', wdata)[0]
        wdata = re.subn('.\x7f', '', wdata)[0]
        data = wdata.encode('utf-8')
        req = urllib.request.Request(url, data=data)
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        with urllib.request.urlopen(req) as conn:
            result = conn.read().decode('utf-8')
            print(result)
        if cmd:
            break
    except Exception as ex:
        print("ERROR:: %s" % str(ex))
        traceback.print_exc()


# vim: ts=4 sw=4 sts=4 expandtab
