from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch

import cgi
import tempfile
# import win32api
import copy
import os
import glob
import sys


class DWPrinter:
    def __init__(self, args):
        self.source_file_name = None
        self.source_file = None
        self.lastCr = False
        self.printFormat = args.printFormat
        # `self.printMode = args.printMode
        self.printDir = args.printDir if args.printDir else None
        self.printFile = args.printFile if args.printFile else None
        self.printCmd = args.printCmd
        self.printPrefix = args.printPrefix
        self.spoolNum = 1
        print self.printDir, self.printFile, self.printCmd, self.printPrefix

    def _getNextSpoolFile(self, extension=None):
        if not extension:
            extension = self.printFormat

        if not self.printDir:
            return 'cocoprints.%s' % extension

        g = glob.glob(os.path.join(self.printDir, "%s*" % self.printPrefix))
        if g:
            g.sort()
            try:
                self.spoolNum = int(os.path.basename(g[-1]).split('.')[0][len(self.printPrefix):])
                self.spoolNum += 1
            except:
                pass
        return os.path.join(self.printDir, "%s%04d.%s" % (self.printPrefix, self.spoolNum, extension))

    def write(self, data, dropCr=True):
        if not self.source_file:
            if self.printFormat is 'pdf':
                self.source_file_name = tempfile.mktemp(".txt")
            elif self.printFile:
                self.source_file_name = self.printFile
            elif self.printDir:
                self.source_file_name = self._getNextSpoolFile()
            else:
                self.source_file_name = tempfile.mktemp(".txt")
            self.source_file = open(self.source_file_name, "w")
            #print(
            #    "Printing: opening print buffer: %s" %
            #    (self.source_file_name))
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
        # print("Printing: closing print buffer: %s" % (self.source_file_name))
        printFileName = None
        if self.printFormat == 'pdf':
            printFileName = self._doPrintingPdf()
            os.unlink(self.source_file_name)
        else:
            #print("Closing Spool File: %s" % (self.source_file_name))
            printFileName = self.source_file_name
        if printFileName:
            print("Printing Complete: %s" % (printFileName))
        if printFileName and self.printCmd:
            cmd = '%s %s' % (self.printCmd, printFileName)
            print("Running Command: %s" % cmd)
            os.system(cmd)
        self.printReset()

    def _getFontPath(self, font):
        if getattr(sys, 'frozen', False):
            # we are running in a bundle
            bundle_dir = sys._MEIPASS
        else:
            # we are running in a normal Python environment
            bundle_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(bundle_dir, font)

    def _doPrintingPdf(self):
        if self.printFile:
            pdf_file_name = self.printFile
        elif self.printDir:
            pdf_file_name = self._getNextSpoolFile(extension='pdf')
        else:
            pdf_file_name = tempfile.mktemp(".pdf")
        # print("Printing to: %s" % (pdf_file_name))

        # ## FONT # ##
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        pdfmetrics.registerFont(TTFont('Epson1', self._getFontPath('fonts/epson1.ttf')))
        pdfmetrics.registerFontFamily('Epson1', normal='Epson1')
        # ## FONT # ##

        styles = getSampleStyleSheet()
        code = styles["Code"]
        pre = code.clone('Pre', leftIndent=0, fontName='Epson1')
        normal = styles["Normal"]
        styles.add(pre)

        doc = SimpleDocTemplate(pdf_file_name)
        story = [Preformatted(open(self.source_file_name).read(), pre)]
        doc.build(story)
        # win32api.ShellExecute (0, "print", pdf_file_name, None, ".", 0)
        return pdf_file_name


# vim: ts=4 sw=4 sts=4 expandtab
