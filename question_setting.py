from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QTabWidget, QPushButton, QLabel, QLineEdit,QSpacerItem, QFileDialog, QTextEdit,  QSizePolicy, QCheckBox, QGroupBox, QRadioButton, QSpinBox, QPlainTextEdit, QMessageBox
from PySide6.QtCore import QObject, Signal, Slot, Qt
import sqlite3
import os 

class QuestionSetting(QWidget):
    def __init__(self):
        super().__init__()
       
        self.setWindowTitle("Question Setting")
        
        self.question_button = QuestionButton()
        self.input_area = InputArea()

        


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

        # Question types boolean, add to Database
        self.multiple_choice_bool = False
        self.true_or_false_bool = False
        self.identification_bool = False
        self.essay_bool = False



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
        self.english = QRadioButton("English")
        self.filipino = QRadioButton("Filipino")

        # Language variable
        self.language_chosen = ""


        # When radio button is clicked
        self.english.clicked.connect(self.language_chosen_english)
        self.filipino.clicked.connect(self.language_chosen_filipino)
        

        language_vlayout = QVBoxLayout()
        language_vlayout.addWidget(language_label)
        language_vlayout.addWidget(self.english)
        language_vlayout.addWidget(self.filipino)
        language.setLayout(language_vlayout)


        question.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
  
        language.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        





        v_layout = QVBoxLayout()
        h_layout = QHBoxLayout()

        h_layout.addWidget(question)
        h_layout.addLayout(qty_vlayout)
        h_layout.addWidget(language)




        v_layout.addWidget(self.input_area)
        v_layout.addLayout(h_layout)
        v_layout.addWidget(self.question_button)

        self.setLayout(v_layout)

        self.question_button.generate_question_button.clicked.connect(self.get_question)

    def language_chosen_english(self):
        if self.english.isChecked():
            self.language_chosen = "English"
            print(self.language_chosen)

    def language_chosen_filipino(self):
        if self.filipino.isChecked():
            self.language_chosen = "Filipino"
            print(self.language_chosen)
            

    def get_question(self):
        self.multiple_choice_bool = self.multiple_choice_bool
        self.true_or_false_bool = self.true_or_false_bool
        self.identification_bool = self.identification_bool
        self.essay_bool = self.essay_bool
        self.file = self.input_area.textbox.text()
        self.text_input = self.input_area.input_message.toPlainText()


        print('\n\n')
        print('File:', self.file)
        print('Text input:', self.text_input)

        print('-- Question Types and Amount--\n\n')
        print('Multiple choice:',self.multiple_choice_bool)
        print('True or false:',self.true_or_false_bool)
        print('Identification:',self.identification_bool)
        print('Essay:',self.essay_bool)
        print('')

        self.multiple_choice_qty = self.multiple_choice_qty
        self.true_or_false_qty = self.true_or_false_qty
        self.identification_qty = self.identification_qty
        self.essay_qty = self.essay_qty

        print('Multiple choice amount:',self.multiple_choice_qty)
        print('True or false amount:',self.true_or_false_qty)
        print('Identification amount:',self.identification_qty)
        print('Essay amount:',self.essay_qty)
        print('')

        self.language_chosen = self.language_chosen
        print("Language:",self.language_chosen)

        if self.file == "" and self.text_input == "":
            button = QMessageBox.critical(
            self,
            "Error!",
            " No file or text input found.\nPlease input a file or text message.",
            buttons=QMessageBox.Ignore,
            defaultButton=QMessageBox.Ignore,
        )
           

            if button == QMessageBox.Ignore:
                print("Ignore")

        if self.language_chosen == "":
            button = QMessageBox.critical(
            self,
            "Error!",
            "No language selected.\nPlease select a language.",
            buttons=QMessageBox.Ignore,
            defaultButton=QMessageBox.Ignore,
        )

            if button == QMessageBox.Ignore:
                print("Ignore")





        
    # Signal Modules
    def multiple_box_toggled(self,checked): 
        if checked:
            self.multiple_choice_spinbox.setDisabled(False)
            self.multiple_choice_bool = True
            print(self.multiple_choice_bool)
            self.multiple_choice_spinbox.setMinimum(1)
        else:
            self.multiple_choice_spinbox.setDisabled(True)
            self.multiple_choice_spinbox.setMinimum(0)
            self.multiple_choice_spinbox.setValue(0)
            self.multiple_choice_bool = False
            print(self.multiple_choice_bool)


    def trueorfalse_box_toggled(self,checked): 
        if checked:
            self.true_or_false_spinbox.setDisabled(False)
            self.true_or_false_bool = True
            print(self.multiple_choice_bool)
            self.true_or_false_spinbox.setMinimum(1)
        else:
            self.true_or_false_spinbox.setDisabled(True)
            self.true_or_false_bool = False
            print(self.multiple_choice_bool)
            self.true_or_false_spinbox.setMinimum(0)
            self.true_or_false_spinbox.setValue(0)

    def identification_box_toggled(self,checked): 
        if checked:
            self.identification_spinbox.setDisabled(False)
            self.identification_bool = True
            print(self.multiple_choice_bool)
            self.identification_spinbox.setMinimum(1)
        else:
            self.identification_spinbox.setDisabled(True)
            self.identification_bool = False
            print(self.multiple_choice_bool)
            self.identification_spinbox.setMinimum(0)
            self.identification_spinbox.setValue(0)


    def essay_box_toggled(self,checked): 
        if checked:
            self.essay_spinbox.setDisabled(False)
            self.essay_bool = True
            print(self.multiple_choice_bool)
            self.essay_spinbox.setMinimum(1)
        else:
            self.essay_spinbox.setDisabled(True)
            self.essay_bool = False
            print(self.multiple_choice_bool)
            self.essay_spinbox.setMinimum(0)
            self.essay_spinbox.setValue(0)


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

        # Question Amount, add to Database
        self.multiple_choice_qty = self.multiple_choice_spinbox.value()
        self.true_or_false_qty = self.true_or_false_spinbox.value()
        self.identification_qty = self.identification_spinbox.value()
        self.essay_qty = self.essay_spinbox.value()

        self.multiple_choice_spinbox.valueChanged.connect(self.multiple_choice_qty_changed)
        self.true_or_false_spinbox.valueChanged.connect(self.true_or_false_qty_changed)
        self.identification_spinbox.valueChanged.connect(self.identification_qty_changed) 
        self.essay_spinbox.valueChanged.connect(self.essay_qty_changed) 

    # Changes and gets multiple choice spinbox amount
    def multiple_choice_qty_changed(self, i):
        self.multiple_choice_qty = i
        print(self.multiple_choice_qty)

        # Minimum value of spinbox is 1 not 0


    # Changes and gets true or false spinbox amount
    def true_or_false_qty_changed(self, i):
        self.true_or_false_qty = i
        print(self.true_or_false_qty)
        

    # Changes and gets identification spinbox amount
    def identification_qty_changed(self, i):
        self.identification_qty = i
        print(self.identification_qty)
        

    # Changes and gets essay spinbox amount
    def essay_qty_changed(self, i):
        self.essay_qty = i
        print(self.essay_qty)
        








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
        self.setMinimum(0)
        #self.setValue(1)
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


        self.textbox = QLabel()
        self.textbox.setDisabled(True)
        self.textbox.setStyleSheet("padding:8px;font-size: 14px;")
        self.textbox.setMinimumHeight(400)
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
        self.input_message = QPlainTextEdit()
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
        self.response = QFileDialog.getOpenFileName(
            parent=self,
            caption='Select a file',
            dir=os.getcwd(),
            filter=file_filter,
            selectedFilter='Word File (*.docx *.doc)'
        )
        print(self.response)
        self.textbox.setText(self.response[0])
        self.input_file.setText("Update File")
        self.tab_widget.setTabEnabled(1, False)
        return self.response

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


        print("Insert data succesfully")
        self.connection.commit()
        self.connection.close()
        

