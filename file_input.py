from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QTabWidget, QPushButton, QLabel, QLineEdit,QSpacerItem, QFileDialog, QTextEdit,  QSizePolicy

class InputArea(QWidget):
    def __init__(self):
        super().__init__()
       

        tab_widget = QTabWidget(self)


        widget_file = QWidget()
        label_file = QLabel("Input (PDF, DOC, or DOCX) file :")
        input_file = QFileDialog()


        form_layout = QVBoxLayout()
        form_layout.addWidget(label_file)
        form_layout.addWidget(input_file)
        widget_file.setLayout(form_layout)


        widget_text_input = QWidget()
        self.input_message = QTextEdit()  # Changed: Make it an instance attribute

        text_input_layout = QVBoxLayout()
        text_input_layout.addWidget(self.input_message)  # Changed: Use self.input_message
        widget_text_input.setLayout(text_input_layout)


        #Add tabs to widget
        tab_widget.addTab(widget_file,"File")
        tab_widget.addTab(widget_text_input,"Text")


        layout = QVBoxLayout()
        layout.addWidget(tab_widget)

        widget_file.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        widget_text_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)


        self.setLayout(layout)


    def button_1_clicked(self):
        print("Button clicked")