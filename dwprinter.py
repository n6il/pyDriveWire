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
    def __init__(self):
        self.source_file_name = None
        self.source_file = None

    def write(self, data, dropCr=True):
        if not self.source_file:
            self.source_file_name = tempfile.mktemp (".txt")
            self.source_file = open(self.source_file_name, "w")
            print("Printing: opening print buffer: %s" % (self.source_file_name))
        if data != '\r':
            self.source_file.write(data)

    def printFlush(self):
        self.source_file.close()
        self.source_file = None
        self._doPrinting()
        print("Printing: closing print buffer: %s" % (self.source_file_name))
        os.unlink(self.source_file_name)
        self.source_file_name = None

    def _doPrinting(self):
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
