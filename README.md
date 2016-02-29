# pyDriveWire
Python Implementation of DriveWire 4

Run It
------
    python ./pyDriveWire.py <serial_dev> <speed>  <drive_0_disk_image>

Example from the author that he usese on the Coco3FPGA board.  Note that 4800 baud is really
mapped to 921,600 baud:

    python ./pyDriveWire.py /dev/tty.usbserial-FTF4ZN9S 4800 nos96809l2v030300coco3_becker.dsk

Supported DW Commands
---------------------
* `dw show`   ->  `dw disk show`
* `dw insert <d> <p>` ->  `dw disk insert <d> <p>`
* `dw eject <d>` -> `dw disk eject <p>`
* `dw dir <p>` -> `dw server dir <p>`
* `dw list <p>` -> `dw server list <p>`
