from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QHBoxLayout
import sys
import sqlite3

from question_setting import QuestionSetting
from file_input import InputArea
from ai_output import OutputArea
from question_setting import SideBarNotebook
from question_setting import QuestionSettingDB

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
    output_area = OutputArea()
    sidebar_notebook = SideBarNotebook()

    

    # Database for question setting
    question_setting_database = QuestionSettingDB()


    # Get generate question button
    #question_setting.question_button.generate_question_button.clicked.connect()

    # Question input layout
    question_input_layout = QVBoxLayout()
    question_input_layout.addWidget(input_area)
    question_input_layout.addWidget(question_setting)

    # AI Model output layout
    ai_output_layout = QVBoxLayout()
    ai_output_layout.addWidget(output_area)

    # Sidebar Layout for Notebook Saving
    sidebar_notebook_layout = QVBoxLayout()
    sidebar_notebook_layout.addWidget(sidebar_notebook)
    

    notebook_layout = QHBoxLayout()
    notebook_layout.addLayout(sidebar_notebook_layout)
    notebook_layout.addLayout(question_input_layout)
    notebook_layout.addLayout(ai_output_layout)

    notebook.setLayout(notebook_layout)





    window = notebook

    window.show()
    app.exec()