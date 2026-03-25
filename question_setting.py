import os
import sys
from typing import Dict, List

from extract_text import ExtractText
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QCheckBox,
    QMenu,
)


class QuestionSetting(QWidget):
    generate_requested = Signal(dict)
    save_notebook_requested = Signal(dict)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Question Setting")

        self.question_button = QuestionButton()
        self.input_area = InputArea()

        question_group = QGroupBox()
        question_group.setStyleSheet("border:0;")

        self.multiple_choice = QCheckBox("Multiple Choice")
        self.true_or_false = QCheckBox("True or False")
        self.identification = QCheckBox("Identification")
        self.essay = QCheckBox("Essay")

        for checkbox in [self.multiple_choice, self.true_or_false, self.identification, self.essay]:
            checkbox.setStyleSheet("font-size:14px;")

        self.multiple_choice.toggled.connect(self._multiple_box_toggled)
        self.true_or_false.toggled.connect(self._trueorfalse_box_toggled)
        self.identification.toggled.connect(self._identification_box_toggled)
        self.essay.toggled.connect(self._essay_box_toggled)

        self._initialize_spinboxes()

        qty_layout = QVBoxLayout()
        self._question_spinbox_layout(
            qty_layout,
            self.multiple_choice_spinbox,
            self.true_or_false_spinbox,
            self.identification_spinbox,
            self.essay_spinbox,
        )

        question_vlayout = QVBoxLayout()
        question_layout = QHBoxLayout()
        self._question_checkbox_layout(
            self.multiple_choice,
            self.true_or_false,
            self.identification,
            self.essay,
            question_vlayout,
        )
        question_layout.addLayout(question_vlayout)
        question_group.setLayout(question_layout)

        language_group = QGroupBox()
        language_label = QLabel("Select Language")
        language_label.setStyleSheet("font-size:16px;")
        language_group.setStyleSheet("border:0;")
        self.english = QRadioButton("English")
        self.filipino = QRadioButton("Filipino")
        self.language_chosen = ""

        self.english.clicked.connect(self._language_chosen_english)
        self.filipino.clicked.connect(self._language_chosen_filipino)

        language_vlayout = QVBoxLayout()
        language_vlayout.addWidget(language_label)
        language_vlayout.addWidget(self.english)
        language_vlayout.addWidget(self.filipino)
        language_group.setLayout(language_vlayout)

        question_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        language_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        content_layout = QVBoxLayout()
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(question_group)
        filter_layout.addLayout(qty_layout)
        filter_layout.addWidget(language_group)

        content_layout.addWidget(self.input_area)
        content_layout.addLayout(filter_layout)
        content_layout.addWidget(self.question_button)
        self.setLayout(content_layout)

        self.question_button.generate_question_button.clicked.connect(self._on_generate_clicked)
        self.question_button.save_as_button.clicked.connect(self._on_save_clicked)

    def collect_payload(self) -> Dict:
        return {
            "file_input": self.input_area.textbox.text().strip(),
            "text_input": self.input_area.input_message.toPlainText().strip(),
            "input_content": self.input_area.get_input_content(),
            "input_error": self.input_area.last_input_error,
            "multiple_choice_bool": self.multiple_choice.isChecked(),
            "true_or_false_bool": self.true_or_false.isChecked(),
            "identification_bool": self.identification.isChecked(),
            "essay_bool": self.essay.isChecked(),
            "multiple_choice_qty": self.multiple_choice_spinbox.value(),
            "true_or_false_qty": self.true_or_false_spinbox.value(),
            "identification_qty": self.identification_spinbox.value(),
            "essay_qty": self.essay_spinbox.value(),
            "language": self.language_chosen,
        }

    def set_from_saved_settings(self, settings: Dict):
        self.input_area.load_saved_input(settings.get("file_input", ""), settings.get("text_input", ""))

        self.multiple_choice.setChecked(bool(settings.get("multiple_choice_bool", False)))
        self.true_or_false.setChecked(bool(settings.get("true_or_false_bool", False)))
        self.identification.setChecked(bool(settings.get("identification_bool", False)))
        self.essay.setChecked(bool(settings.get("essay_bool", False)))

        self.multiple_choice_spinbox.setValue(int(settings.get("multiple_choice_qty", 0)))
        self.true_or_false_spinbox.setValue(int(settings.get("true_or_false_qty", 0)))
        self.identification_spinbox.setValue(int(settings.get("identification_qty", 0)))
        self.essay_spinbox.setValue(int(settings.get("essay_qty", 0)))

        language = settings.get("language", "")
        self.english.setChecked(language == "English")
        self.filipino.setChecked(language == "Filipino")
        self.language_chosen = language

    def reset_to_defaults(self):
        self.input_area.reset_inputs()

        self.multiple_choice.setChecked(False)
        self.true_or_false.setChecked(False)
        self.identification.setChecked(False)
        self.essay.setChecked(False)

        self.multiple_choice_spinbox.setValue(0)
        self.true_or_false_spinbox.setValue(0)
        self.identification_spinbox.setValue(0)
        self.essay_spinbox.setValue(0)

        self.english.setAutoExclusive(False)
        self.filipino.setAutoExclusive(False)
        self.english.setChecked(False)
        self.filipino.setChecked(False)
        self.english.setAutoExclusive(True)
        self.filipino.setAutoExclusive(True)
        self.language_chosen = ""

    def ask_notebook_name(self) -> str:
        notebook_name, ok = QInputDialog.getText(self, "Save Notebook", "Notebook name:")
        if not ok:
            return ""
        return notebook_name.strip()

    def _on_generate_clicked(self):
        payload = self.collect_payload()
        validation_error = self._validate_payload(payload)
        if validation_error:
            QMessageBox.critical(self, "Error!", validation_error, buttons=QMessageBox.Ignore, defaultButton=QMessageBox.Ignore)
            return

        self.generate_requested.emit(payload)

    def _on_save_clicked(self):
        payload = self.collect_payload()
        self.save_notebook_requested.emit(payload)

    def _validate_payload(self, payload: Dict) -> str:
        if not payload["input_content"]:
            if payload.get("input_error"):
                return payload["input_error"]
            return "No file or text input found.\nPlease input a file or text message."

        if not payload["language"]:
            return "No language selected.\nPlease select a language."

        total_selected = (
            payload["multiple_choice_qty"]
            + payload["true_or_false_qty"]
            + payload["identification_qty"]
            + payload["essay_qty"]
        )
        if total_selected <= 0:
            return "No question amount selected.\nPlease choose at least one question type and quantity."

        return ""

    def _language_chosen_english(self):
        if self.english.isChecked():
            self.language_chosen = "English"

    def _language_chosen_filipino(self):
        if self.filipino.isChecked():
            self.language_chosen = "Filipino"

    def _initialize_spinboxes(self):
        self.multiple_choice_spinbox = SpinBox()
        self.true_or_false_spinbox = SpinBox()
        self.identification_spinbox = SpinBox()
        self.essay_spinbox = SpinBox()

        for spinbox in [
            self.multiple_choice_spinbox,
            self.true_or_false_spinbox,
            self.identification_spinbox,
            self.essay_spinbox,
        ]:
            spinbox.setDisabled(True)

    def _multiple_box_toggled(self, checked):
        self.multiple_choice_spinbox.setDisabled(not checked)
        self.multiple_choice_spinbox.setMinimum(1 if checked else 0)
        if not checked:
            self.multiple_choice_spinbox.setValue(0)

    def _trueorfalse_box_toggled(self, checked):
        self.true_or_false_spinbox.setDisabled(not checked)
        self.true_or_false_spinbox.setMinimum(1 if checked else 0)
        if not checked:
            self.true_or_false_spinbox.setValue(0)

    def _identification_box_toggled(self, checked):
        self.identification_spinbox.setDisabled(not checked)
        self.identification_spinbox.setMinimum(1 if checked else 0)
        if not checked:
            self.identification_spinbox.setValue(0)

    def _essay_box_toggled(self, checked):
        self.essay_spinbox.setDisabled(not checked)
        self.essay_spinbox.setMinimum(1 if checked else 0)
        if not checked:
            self.essay_spinbox.setValue(0)

    def _question_spinbox_layout(
        self,
        qty_vlayout,
        multiple_choice_spinbox,
        true_or_false_spinbox,
        identification_spinbox,
        essay_spinbox,
    ):
        qty_vlayout.addWidget(multiple_choice_spinbox)
        qty_vlayout.addWidget(true_or_false_spinbox)
        qty_vlayout.addWidget(identification_spinbox)
        qty_vlayout.addWidget(essay_spinbox)

    def _question_checkbox_layout(self, multiple_choice, true_or_false, identification, essay, question_vlayout):
        question_vlayout.addWidget(multiple_choice)
        question_vlayout.addWidget(true_or_false)
        question_vlayout.addWidget(identification)
        question_vlayout.addWidget(essay)


class SpinBox(QSpinBox):
    def __init__(self):
        super().__init__()
        self.setMaximum(10)
        self.setMinimum(0)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)


class QuestionButton(QWidget):
    def __init__(self):
        super().__init__()

        self.save_as_button = QPushButton("Save as Notebook")
        self.save_as_button.setStyleSheet("padding: 8px; font-size: 14px;")

        self.generate_question_button = QPushButton("Generate Question")
        self.generate_question_button.setStyleSheet("padding: 8px; font-size: 14px;")

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.save_as_button)
        button_layout.addWidget(self.generate_question_button)
        self.setLayout(button_layout)


class SideBarNotebook(QWidget):
    notebook_selected = Signal(int)
    notebook_delete_requested = Signal(int)
    notebook_rename_requested = Signal(int)
    notebook_new_requested = Signal()

    def __init__(self):
        super().__init__()

        self.setMinimumWidth(300)

        notebook_label = QLabel("Notebook")
        notebook_label.setAlignment(Qt.AlignCenter)
        notebook_label.setStyleSheet("font-size: 16px; text-align: center;")

        self.new_notebook_button = QPushButton("New Notebook")
        self.new_notebook_button.setStyleSheet("padding: 8px; font-size: 14px;")
        self.new_notebook_button.clicked.connect(lambda _: self.notebook_new_requested.emit())

        self.mode_label = QLabel()
        self.mode_label.setAlignment(Qt.AlignCenter)
        self.mode_label.setStyleSheet("font-size: 12px; color: #777;")

        self.list_container = QWidget()
        self.list_layout = QVBoxLayout()
        self.list_layout.setAlignment(Qt.AlignTop)
        self.list_container.setLayout(self.list_layout)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.list_container)

        sidebar_layout = QVBoxLayout()
        sidebar_layout.setAlignment(Qt.AlignTop)
        sidebar_layout.addWidget(notebook_label)
        sidebar_layout.addWidget(self.new_notebook_button)
        sidebar_layout.addWidget(self.mode_label)
        sidebar_layout.addWidget(self.scroll)
        self.setLayout(sidebar_layout)

        self.set_new_notebook_mode(True)

    def set_new_notebook_mode(self, is_new_mode: bool, notebook_name: str = ""):
        if is_new_mode:
            self.mode_label.setText("Mode: New Notebook (unsaved)")
            return

        display_name = notebook_name.strip() or "Saved Notebook"
        self.mode_label.setText(f"Mode: {display_name}")

    def set_notebooks(self, notebooks: List[Dict]):
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        if not notebooks:
            empty_label = QLabel("No saved notebooks yet")
            empty_label.setAlignment(Qt.AlignCenter)
            self.list_layout.addWidget(empty_label)
            return

        for notebook in notebooks:
            notebook_row = QWidget()
            row_layout = QHBoxLayout()
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(6)

            button = QPushButton(notebook["name"])
            button.setStyleSheet("padding: 8px; text-align: left;")
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            button.clicked.connect(lambda _, notebook_id=notebook["id"]: self.notebook_selected.emit(notebook_id))

            menu_button = QToolButton()
            menu_button.setText("⋯")
            menu_button.setPopupMode(QToolButton.InstantPopup)
            menu_button.setStyleSheet("padding: 4px 8px; font-size: 16px;")

            menu = QMenu(menu_button)
            rename_action = menu.addAction("Rename")
            rename_action.triggered.connect(
                lambda _, notebook_id=notebook["id"]: self.notebook_rename_requested.emit(notebook_id)
            )
            delete_action = menu.addAction("Delete")
            delete_action.triggered.connect(
                lambda _, notebook_id=notebook["id"]: self.notebook_delete_requested.emit(notebook_id)
            )
            menu_button.setMenu(menu)

            row_layout.addWidget(button)
            row_layout.addWidget(menu_button)
            notebook_row.setLayout(row_layout)

            self.list_layout.addWidget(notebook_row)


class InputArea(QWidget):
    def __init__(self):
        super().__init__()

        self.last_input_error = ""

        self.tab_widget = QTabWidget(self)

        widget_file = QWidget()
        label_file = QLabel("Input (PDF, DOC, DOCX, or PPT) file :")
        label_file.setStyleSheet("font-size: 14px;")

        self.input_file = QPushButton("Choose File")
        self.input_file.setStyleSheet("padding:8px;font-size: 14px; text-align: center;")
        self.input_file.clicked.connect(self.getFileName)

        self.textbox = QLabel()
        self.textbox.setDisabled(True)
        self.textbox.setStyleSheet("padding:8px;font-size: 14px;")
        self.textbox.setMinimumHeight(400)

        self.remove_file = QPushButton("Remove File")
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

        self.tab_widget.addTab(widget_file, "File")
        self.tab_widget.addTab(widget_text_input, "Text")

        layout = QVBoxLayout()
        layout.addWidget(self.tab_widget)

        widget_file.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        widget_text_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        widget_file.setMinimumSize(600, 500)
        widget_text_input.setMinimumSize(600, 500)

        self.setLayout(layout)

    def getFileName(self):
        file_filter = "Word File (*.docx *.doc);; PDF (*.pdf);; Presentation (*.pptx *.ppt);; Text File (*.txt)"
        response = QFileDialog.getOpenFileName(
            parent=self,
            caption="Select a file",
            dir=os.getcwd(),
            filter=file_filter,
            selectedFilter="Word File (*.docx *.doc)",
        )
        self.textbox.setText(response[0])
        self.input_file.setText("Update File")
        self.tab_widget.setTabEnabled(1, False)

    def removeFileName(self):
        self.tab_widget.setTabEnabled(1, True)
        self.input_file.setText("Choose File")
        self.textbox.setText("")

    def isEmpty(self):
        text = self.input_message.toPlainText()
        self.tab_widget.setTabEnabled(0, text == "")

    def get_input_content(self) -> str:
        self.last_input_error = ""
        file_path = self.textbox.text().strip()
        text_input = self.input_message.toPlainText().strip()

        if text_input:
            return text_input

        if not file_path:
            return ""

        supported_extensions = (".txt", ".pdf", ".doc", ".docx", ".ppt", ".pptx")
        if file_path.lower().endswith(supported_extensions):
            try:
                return ExtractText(file_path).convert()
            except OSError:
                self.last_input_error = "Could not open the selected file. Please verify the path and permissions."
                return ""
            except RuntimeError as error:
                self.last_input_error = f"{error}\nPython: {sys.executable}"
                return ""
            except Exception:
                self.last_input_error = (
                    "Failed to extract text from the selected file. "
                    "For PDF/DOCX/PPTX support, install: pymupdf python-docx python-pptx"
                )
                return ""

        self.last_input_error = "Unsupported file type. Please use TXT, PDF, DOC/DOCX, or PPT/PPTX."
        return ""

    def load_saved_input(self, file_input: str, text_input: str):
        if text_input:
            self.removeFileName()
            self.input_message.setPlainText(text_input)
            self.tab_widget.setCurrentIndex(1)
            return

        self.input_message.setPlainText("")
        self.tab_widget.setTabEnabled(1, True)

        if file_input:
            self.textbox.setText(file_input)
            self.input_file.setText("Update File")
            self.tab_widget.setTabEnabled(1, False)
            self.tab_widget.setCurrentIndex(0)
        else:
            self.removeFileName()

    def reset_inputs(self):
        self.last_input_error = ""
        self.input_message.setPlainText("")
        self.removeFileName()
        self.tab_widget.setCurrentIndex(0)
