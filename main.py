from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
import sys

from question_setting import QuestionSetting
from file_input import InputArea

# class MainWindow(QMainWindow):
#     def __init__(self, app):
#         super().__init__()
#         self.app = app
#         question_setting = QuestionSetting()
#         input_area = InputArea()
       
#         widget = QWidget()
#         v_layout = QVBoxLayout()
#         v_layout.addWidget(question_setting)
#         v_layout.addWidget(input_area)
#         widget.setLayout(v_layout)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    notebook = QWidget()
    question_setting = QuestionSetting()
    input_area = InputArea()

    question_input_layout = QVBoxLayout()
    question_input_layout.addWidget(input_area)
    question_input_layout.addWidget(question_setting)

    notebook.setLayout(question_input_layout)





    window = notebook

    window.show()
    app.exec()