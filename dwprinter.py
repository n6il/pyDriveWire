from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch

import cgi
import tempfile
#import win32api
import copy
import os

class DWPrinter:
    def __init__(self, args):
        self.source_file_name = None
        self.source_file = None
        self.lastCr = False
        self.printFormat = args.printFormat
        #`self.printMode = args.printMode
        self.printDir = args.printDir if args.printDir else None
        self.printFile = args.printFile if args.printFile else None
        self.printCmd = args.printCmd

    def write(self, data, dropCr=True):
        if not self.source_file:
            if self.printFile:
               self.source_file_name = self.printFile
            elif self.printDir:
               self.source_file_name = tempfile.mktemp (".txt", self.printDir)
            else:
               self.source_file_name = tempfile.mktemp (".txt")
            self.source_file = open(self.source_file_name, "w")
            print("Printing: opening print buffer: %s" % (self.source_file_name))
        if data == '\r':
            self.source_file.write('\n')
            self.lastCr = True
        elif data == '\n':
            if not self.lastCr:
                self.source_file.write(data)
            self.lastCr = False
        else:
            self.source_file.write(data)
            self.lastCr = False

    def printReset(self):
        self.source_file = None
        self.source_file_name = None

    def printFlush(self):
        if not self.source_file:
            return
        self.source_file.close()
        #print("Printing: closing print buffer: %s" % (self.source_file_name))
        printFileName = None
        if self.printFormat == 'pdf':
            printFileName = self._doPrintingPdf()
            os.unlink(self.source_file_name)
        else:
            print("Printing to: %s" % (self.source_file_name))
            printFileName = self.source_file_name
        if printFileName and self.printCmd:
            cmd = '%s %s' % (self.printCmd, printFileName)
            print("Running Command: %s" % cmd)
            os.system(cmd)
        self.printReset()

    def _doPrintingPdf(self):
        if self.printDir:
           pdf_file_name = tempfile.mktemp (".pdf", self.printDir)
        else:
           pdf_file_name = tempfile.mktemp (".pdf")
        print("Printing to: %s" % (pdf_file_name))

        ### FONT ###
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        pdfmetrics.registerFont(TTFont('Epson1', 'fonts/epson1.ttf'))
        pdfmetrics.registerFontFamily('Epson1',normal='Epson1')
        ### FONT ###


        styles = getSampleStyleSheet ()
        code = styles["Code"]
        pre = code.clone('Pre', leftIndent=0, fontName='Epson1')
        normal = styles["Normal"]
        styles.add(pre)



        doc = SimpleDocTemplate (pdf_file_name)
        story=[Preformatted(open (self.source_file_name).read(), pre)]
        doc.build (story)
        #win32api.ShellExecute (0, "print", pdf_file_name, None, ".", 0)
        return pdf_file_name
