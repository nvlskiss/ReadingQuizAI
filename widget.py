from PySide6.QtWidgets import QWidget,  QCheckBox, QHBoxLayout, QVBoxLayout, QGroupBox, QRadioButton, QSpinBox, QPushButton,QButtonGroup


class Widget(QWidget):
    def __init__(self):
        super().__init__()
       
        self.setWindowTitle("Question Setting")

        #Checkboxes : operating system
        question = QGroupBox()
        question.setStyleSheet("QGroupBox#theBox {border:0;}")
        question.setStyleSheet("border:0;")

        multiple_choice = QCheckBox("Multiple Choice")
        multiple_choice.toggled.connect(self.multiple_box_toggled)
        multiple_choice.setStyleSheet("font-size:14px;")


        true_or_false = QCheckBox("True or False")
        true_or_false.toggled.connect(self.trueorfalse_box_toggled)
        true_or_false.setStyleSheet("font-size:14px;")

        identification = QCheckBox("Identification")
        identification.toggled.connect(self.identification_box_toggled)
        identification.setStyleSheet("font-size:14px;")

        essay = QCheckBox("Essay")
        essay.toggled.connect(self.essay_box_toggled)
        essay.setStyleSheet("font-size:14px;")

        # Spinboxes
        multiple_choice_spinbox = QSpinBox()
        true_or_false_spinbox = QSpinBox()
        identification_spinbox = QSpinBox()
        essay_spinbox = QSpinBox()


        #Spinboxes layout
        qty_vlayout = QVBoxLayout()
        self.__question_spinbox_layout(qty_vlayout, multiple_choice_spinbox, true_or_false_spinbox, identification_spinbox, essay_spinbox)


        # add Question Widget
        question_vlayout = QVBoxLayout()
        question_layout = QHBoxLayout()
        self.__question_checkbox_layout(multiple_choice, true_or_false, identification, essay, question_vlayout)
        question_layout.addLayout(question_vlayout)
        question.setLayout(question_layout)


        v_layout = QVBoxLayout()
        h_layout = QHBoxLayout()
        h_layout.addWidget(question)
        h_layout.addLayout(qty_vlayout)



        v_layout.addLayout(h_layout)

        self.setLayout(v_layout)

    # Helper modules, makes code simpler
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



    # Signal Modules
    def multiple_box_toggled(self,checked): 
        pass

    def trueorfalse_box_toggled(self,checked): 
        pass

    def identification_box_toggled(self,checked): 
        pass

    def essay_box_toggled(self,checked): 
        pass