from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QSizePolicy, QTabWidget


class OutputArea(QWidget):
    set_changed = Signal(dict)

    def __init__(self):
        super().__init__()

        self.tab_widget = QTabWidget()
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        self._set_payloads = []
        self._loading_sets = False

        layout = QVBoxLayout()
        layout.addWidget(self.tab_widget)
        self.setLayout(layout)

        self.add_set("Set 1", "")

    def _create_output_editor(self, text: str):
        editor = QTextEdit()
        editor.setReadOnly(True)
        editor.setPlainText(text)
        editor.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        editor.setMinimumSize(600, 600)
        return editor

    def add_set(self, set_name: str, generated_output: str, payload: dict | None = None):
        editor = self._create_output_editor(generated_output)
        self.tab_widget.addTab(editor, set_name)
        self._set_payloads.append(payload or {"set_name": set_name, "generated_output": generated_output, "settings": {}})

    def clear_sets(self):
        self.tab_widget.clear()
        self._set_payloads = []

    def load_sets(self, sets: list[dict]):
        self._loading_sets = True
        self.clear_sets()

        if not sets:
            self.add_set("Set 1", "")
        else:
            for item in sets:
                self.add_set(item.get("set_name", "Set"), item.get("generated_output", ""), item)

        self.tab_widget.setCurrentIndex(0)
        self._loading_sets = False

        current_payload = self.get_current_set_payload()
        if current_payload is not None:
            self.set_changed.emit(current_payload)

    def set_active_set(self, set_name: str):
        for index in range(self.tab_widget.count()):
            if self.tab_widget.tabText(index) == set_name:
                self.tab_widget.setCurrentIndex(index)
                return

    def set_output_text(self, text: str):
        if self.tab_widget.count() == 0:
            self.add_set("Set 1", text)
            return

        editor = self.tab_widget.currentWidget()
        if isinstance(editor, QTextEdit):
            editor.setPlainText(text)

        index = self.tab_widget.currentIndex()
        if 0 <= index < len(self._set_payloads):
            self._set_payloads[index]["generated_output"] = text

    def get_output_text(self) -> str:
        editor = self.tab_widget.currentWidget()
        if isinstance(editor, QTextEdit):
            return editor.toPlainText().strip()
        return ""

    def get_current_set_payload(self):
        index = self.tab_widget.currentIndex()
        if 0 <= index < len(self._set_payloads):
            return self._set_payloads[index]
        return None

    def _on_tab_changed(self, index: int):
        if self._loading_sets:
            return

        if 0 <= index < len(self._set_payloads):
            self.set_changed.emit(self._set_payloads[index])
