from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QTabWidget, QPushButton, QLabel, QLineEdit,QSpacerItem, QFileDialog, QTextEdit,  QSizePolicy
import os
from PySide6.QtCore import QObject, Signal, Slot, Qt

class InputArea(QWidget):
    def __init__(self):
        super().__init__()
       

        self.tab_widget = QTabWidget(self)


        widget_file = QWidget()
        label_file = QLabel("Input (PDF, DOC, DOCX, or PPT) file :")
        label_file.setStyleSheet('font-size: 14px;')
        self.input_file = QPushButton()
        self.input_file.setText("Choose File")
        self.input_file.setStyleSheet("padding:8px;font-size: 14px; text-align: center;")
        self.input_file.clicked.connect(self.getFileName)


        self.textbox = QTextEdit()
        self.textbox.setDisabled(True)
        self.textbox.setStyleSheet("padding:8px;font-size: 14px;")
        self.remove_file = QPushButton()
        self.remove_file.setText("Remove File")
        self.remove_file.setStyleSheet("padding:8px;font-size: 14px; text-align: center;")
        self.remove_file.clicked.connect(self.removeFileName)



        


        form_layout = QVBoxLayout()
        form_layout.addWidget(label_file)
        form_layout.addWidget(self.input_file)
        form_layout.addWidget(self.textbox)
        form_layout.addWidget(self.remove_file)
        form_layout.setAlignment(Qt.AlignTop)
        widget_file.setLayout(form_layout)


        widget_text_input = QWidget()
        self.input_message = QTextEdit()
        self.input_message.textChanged.connect(self.isEmpty)

        text_input_layout = QVBoxLayout()
        text_input_layout.addWidget(self.input_message)
        widget_text_input.setLayout(text_input_layout)


        #Add tabs to widget
        self.tab_widget.addTab(widget_file,"File")
        self.tab_widget.addTab(widget_text_input,"Text")


        layout = QVBoxLayout()
        layout.addWidget(self.tab_widget)

        widget_file.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        widget_text_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        widget_file.setMinimumSize(600,500)
        widget_text_input.setMinimumSize(600,500)

        self.setLayout(layout)

    def getFileName(self):
        file_filter = "Word File (*.docx *.doc);; PDF (*.pdf);; Presentation (*.pptx *.ppt);; Text File (*.txt)"
        response = QFileDialog.getOpenFileName(
            parent=self,
            caption='Select a file',
            dir=os.getcwd(),
            filter=file_filter,
            selectedFilter='Word File (.docx ,.doc)|*.docx;*.doc'
        )
        print(response)
        self.textbox.setText(response[0])
        self.input_file.setText("Update File")
        self.tab_widget.setTabEnabled(1, False)
        

    def removeFileName(self):
        self.tab_widget.setTabEnabled(1, True)
        self.input_file.setText("Choose File")
        self.textbox.setText("")
        print("File Cancelled")

    def isEmpty(self):
        text = self.input_message.toPlainText()
        if text != "":
            self.tab_widget.setTabEnabled(0, False)
        else:
            self.tab_widget.setTabEnabled(0, True)
