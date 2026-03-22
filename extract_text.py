import csv
import pymupdf
import docx
from pptx import Presentation

class ExtractText:
    def __init__(self, path):
        self.path = path
        # TEXT OUTPUT OF PATH
        self.text_format = ""


        # Check if file type is a Text File
        if ".txt" in self.path:
            self.text_file(path)
            print(self.text_format)
            
        # Check if file type is a PDF File
        if ".pdf" in self.path:
            self.pdf_file(path)
            print(self.text_format)
            
        # Check if file type is a PDF File
        if ".doc" in self.path:
            self.doc_file(path)
            print(self.text_format)

        # Check if file type is a PDF File
        if ".ppt" in self.path:
            self.ppt_file(path)
            print(self.text_format)
            

    def text_file(self, path):
        with open(path, newline="") as text_file:
            text_reader = csv.reader(text_file)
            for row in text_reader:
                self.text_format +=  "".join(row)

    def pdf_file(self, path):
        doc = pymupdf.open(path)
        for page in doc:
            self.text_format += page.get_text().encode('utf8').decode('utf8')

            self.text_format += (bytes((12,))).decode('utf8')

    def doc_file(self, path):
        doc = docx.Document(path)
        for para in doc.paragraphs:
            self.text_format += para.text

    def ppt_file(self, path):
        prs = Presentation(path)
        text_runs = []

        for slide in prs.slides:
            for shape in slide.shapes:
                if not shape.has_text_frame:
                    continue
                for paragraph in shape.text_frame.paragraphs:
                    for run in paragraph.runs:
                        text_runs.append(run.text)
        self.text_format = "".join(text_runs)

          