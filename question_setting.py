from PySide6.QtWidgets import QWidget,  QCheckBox, QHBoxLayout, QVBoxLayout, QGroupBox, QRadioButton, QSpinBox, QPushButton,QButtonGroup, QSizePolicy, QLabel, QPushButton
from PySide6.QtCore import QObject, Signal, Slot, Qt
import sqlite3



class QuestionSetting(QWidget):
    def __init__(self):
        super().__init__()
       
        self.setWindowTitle("Question Setting")
        
        self.question_button = QuestionButton()


        #Checkboxes
        question = QGroupBox()
        question.setStyleSheet("QGroupBox#theBox {border:0;}")
        question.setStyleSheet("border:0;")

        multiple_choice = QCheckBox("Multiple Choice")
        true_or_false = QCheckBox("True or False")
        identification = QCheckBox("Identification")
        essay = QCheckBox("Essay")

        multiple_choice.toggled.connect(self.multiple_box_toggled)
        multiple_choice.setStyleSheet("font-size:14px;")


        
        true_or_false.toggled.connect(self.trueorfalse_box_toggled)
        true_or_false.setStyleSheet("font-size:14px;")

        
        identification.toggled.connect(self.identification_box_toggled)
        identification.setStyleSheet("font-size:14px;")

        
        essay.toggled.connect(self.essay_box_toggled)
        essay.setStyleSheet("font-size:14px;")

        #Spinboxes
        self.___spinbox_group()
        

        #Spinboxes layout
        qty_vlayout = QVBoxLayout()
        self.__question_spinbox_layout(qty_vlayout, self.multiple_choice_spinbox, self.true_or_false_spinbox, self.identification_spinbox, self.essay_spinbox)


        # add Question Widget
        question_vlayout = QVBoxLayout()
        question_layout = QHBoxLayout()
        self.__question_checkbox_layout(multiple_choice, true_or_false, identification, essay, question_vlayout)
        question_layout.addLayout(question_vlayout)
        question.setLayout(question_layout)


        language = QGroupBox()
        language_label = QLabel("Select Language")
        language_label.setStyleSheet("font-size:16px;")
        language.setStyleSheet("border:0;")
        english = QRadioButton("English")
        filipino = QRadioButton("Filipino")

        language_vlayout = QVBoxLayout()
        language_vlayout.addWidget(language_label)
        language_vlayout.addWidget(english)
        language_vlayout.addWidget(filipino)
        language.setLayout(language_vlayout)


        question.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
  
        language.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        





        v_layout = QVBoxLayout()
        h_layout = QHBoxLayout()

        h_layout.addWidget(question)
        h_layout.addLayout(qty_vlayout)
        h_layout.addWidget(language)





        v_layout.addLayout(h_layout)
        v_layout.addWidget(self.question_button)

        self.setLayout(v_layout)
        
    # Signal Modules
    def multiple_box_toggled(self,checked): 
        if checked:
            self.multiple_choice_spinbox.setDisabled(False)
        else:
            self.multiple_choice_spinbox.setDisabled(True)


    def trueorfalse_box_toggled(self,checked): 
        if checked:
            self.true_or_false_spinbox.setDisabled(False)
        else:
            self.true_or_false_spinbox.setDisabled(True)


    def identification_box_toggled(self,checked): 
        if checked:
            self.identification_spinbox.setDisabled(False)
        else:
            self.identification_spinbox.setDisabled(True)


    def essay_box_toggled(self,checked): 
        if checked:
            self.essay_spinbox.setDisabled(False)
        else:
            self.essay_spinbox.setDisabled(True)


    # Helper modules, makes code simpler
    def ___spinbox_group(self):
        # Spinboxes
        self.multiple_choice_spinbox = SpinBox()
        self.true_or_false_spinbox = SpinBox()
        self.identification_spinbox = SpinBox()
        self.essay_spinbox = SpinBox()

        #Set disabled when starting program
        self.multiple_choice_spinbox.setDisabled(True)
        self.true_or_false_spinbox.setDisabled(True)
        self.identification_spinbox.setDisabled(True)
        self.essay_spinbox.setDisabled(True)

    def __question_spinbox_layout(self, qty_vlayout, multiple_choice_spinbox, true_or_false_spinbox, identification_spinbox, essay_spinbox):
        qty_vlayout.addWidget(multiple_choice_spinbox)
        qty_vlayout.addWidget(true_or_false_spinbox)
        qty_vlayout.addWidget(identification_spinbox)
        qty_vlayout.addWidget(essay_spinbox)


    def __question_checkbox_layout(self, multiple_choice, true_or_false, identification, essay, question_vlayout):
        question_vlayout.addWidget(multiple_choice)
        question_vlayout.addWidget(true_or_false)
        question_vlayout.addWidget(identification)
        question_vlayout.addWidget(essay)


class SpinBox(QSpinBox):
    """Class for the default spinbox"""
    def __init__(self):
        super().__init__()
        self.setMaximum(10)
        self.setMinimum(1)
        self.setValue(1)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

class QuestionButton(QWidget):
    def __init__(self):
        super().__init__()
       
        # Buttons for Question Input
        self.save_as_button = QPushButton()
        self.save_as_button.setText("Save as Notebook")
        self.save_as_button.setStyleSheet("padding: 8px; font-size: 14px;")

        self.generate_question_button = QPushButton()
        self.generate_question_button.setText("Generate Question")
        self.generate_question_button.setStyleSheet("padding: 8px; font-size: 14px;")

        #Button layout
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.save_as_button)
        button_layout.addWidget(self.generate_question_button)

        self.setLayout(button_layout)

class SideBarNotebook(QWidget):
    def __init__(self):
        super().__init__()

        self.setMinimumWidth(300)
        notebook_label = QLabel()
        notebook_label.setText("Notebook")
        notebook_label.setAlignment(Qt.AlignCenter)

        notebook_label.setStyleSheet("font-size: 16px; text-align: center;")


        #Buttons
        notebook = QPushButton()
        notebook.setText("Notebook 1")
        notebook.setStyleSheet("padding: 8px;")

        sidebar_layout = QVBoxLayout()
        sidebar_layout.setAlignment(Qt.AlignTop)
        sidebar_layout.addWidget(notebook_label)
        sidebar_layout.addWidget(notebook)


        self.setLayout(sidebar_layout)    

class QuestionSettingDB:
    def __init__(self):
      pass

    def create_connection(self):
        # Create SQLite Database connection
        self.connection = sqlite3.connect("question_setting.db")

        return self.connection
    
    def insert_data(self, File_input, Input_text, multiple_choice_bool, true_or_false_bool, identification_bool, essay_bool, multiple_choice_qty, true_or_false_qty, identification_qty, essay_qty, language):
        self.cursor = self.create_connection()
        self.cursor.execute("""DROP TABLE IF EXISTS question_setting""")

        self.cursor.execute()

        print("Insert data succesfully")
        self.connection.commit()
        self.connection.close()
        

