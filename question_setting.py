from PySide6.QtWidgets import QWidget,  QCheckBox, QHBoxLayout, QVBoxLayout, QGroupBox, QRadioButton, QSpinBox, QPushButton,QButtonGroup, QSizePolicy, QLabel
from PySide6.QtCore import QObject, Signal, Slot, Qt



class QuestionSetting(QWidget):
    def __init__(self):
        super().__init__()
       
        self.setWindowTitle("Question Setting")
        

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


