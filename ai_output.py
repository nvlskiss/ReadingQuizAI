from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QTabWidget, QPushButton, QLabel, QLineEdit,QSpacerItem, QFileDialog, QTextEdit,  QSizePolicy

class OutputArea(QWidget):
    def __init__(self):
        super().__init__()
       




        ai_output = QWidget()
        output_message = QTextEdit()

        ai_output_layout = QVBoxLayout()
        ai_output_layout.addWidget(output_message)
        ai_output.setLayout(ai_output_layout)



        layout = QVBoxLayout()
        layout.addWidget(ai_output)

        output_message.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        output_message.setMinimumSize(600, 600)

        self.setLayout(layout)


    def button_1_clicked(self):
        print("Button clicked")