import sys
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import QApplication, QHBoxLayout, QMessageBox, QVBoxLayout, QWidget

from ai_output import OutputArea
from database import NotebookDatabase
from question_generator import QuestionGenerator
from question_setting import QuestionSetting, SideBarNotebook


class SplashScreen(QWidget):
    finished = Signal()

    def __init__(self):
        super().__init__()
        self.progress = 0
        self.setFixedSize(420, 320)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_progress)
        self._timer.start(20)

    def showEvent(self, event):
        super().showEvent(event)
        screen = self.screen() or QApplication.primaryScreen()
        if screen:
            geometry = screen.availableGeometry()
            self.move(
                geometry.center().x() - (self.width() // 2),
                geometry.center().y() - (self.height() // 2),
            )

    def _update_progress(self):
        self.progress = min(100, self.progress + 1)
        self.update()
        if self.progress >= 100:
            self._timer.stop()
            QTimer.singleShot(120, self._finish)

    def _finish(self):
        self.finished.emit()
        self.close()

    def paintEvent(self, event):
        _ = event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        circle_size = 220
        x = (self.width() - circle_size) // 2
        y = (self.height() - circle_size) // 2

        shadow_offset = 6
        shadow_size = circle_size + 8
        shadow_x = x - 4 + shadow_offset
        shadow_y = y - 4 + shadow_offset
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 0, 0, 90))
        painter.drawEllipse(shadow_x, shadow_y, shadow_size, shadow_size)

        painter.setPen(Qt.NoPen)
        inner_gap = 18
        fill_x = x + inner_gap
        fill_y = y + inner_gap
        fill_size = circle_size - (inner_gap * 2)
        fill_gradient = QLinearGradient(fill_x, fill_y, fill_x + fill_size, fill_y + fill_size)
        fill_gradient.setColorAt(0.0, QColor("#EDF0D8"))
        fill_gradient.setColorAt(1.0, QColor("#CFE3FF"))
        painter.setBrush(fill_gradient)
        painter.drawEllipse(fill_x, fill_y, fill_size, fill_size)

        base_pen = QPen(QColor("#2c3146"), 12)
        base_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(base_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(x, y, circle_size, circle_size)

        progress_pen = QPen(QColor("#ff5cb8"), 12)
        progress_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(progress_pen)
        start_angle = 90 * 16
        span_angle = int(-360 * 16 * (self.progress / 100.0))
        painter.drawArc(x, y, circle_size, circle_size, start_angle, span_angle)

        painter.setPen(QColor("#111111"))
        painter.setFont(QFont("Segoe UI", 9))
        painter.drawText(x, y + 72, circle_size, 20, Qt.AlignCenter, "ReadingQuizAI")

        painter.setPen(QColor("#ff7ac4"))
        painter.setFont(QFont("Segoe UI", 32, QFont.Bold))
        painter.drawText(x, y + 92, circle_size, 52, Qt.AlignCenter, f"{self.progress}%")

        painter.setPen(QColor("#b7bbca"))
        painter.setFont(QFont("Segoe UI", 10))
        painter.drawText(x, y + 170, circle_size, 20, Qt.AlignCenter, "loading...")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window_icon = None
    logo_path = Path(__file__).resolve().parent / "img" / "READY.png"
    if logo_path.exists():
        window_icon = QIcon(str(logo_path))
        app.setWindowIcon(window_icon)

    notebook = QWidget()
    notebook.setWindowTitle("READY")
    if window_icon is not None:
        notebook.setWindowIcon(window_icon)
    notebook.setObjectName("mainWindow")
    notebook_container_style = "rgba(255, 255, 255, 51)"
    notebook.setStyleSheet(
        "#mainWindow { "
        "background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, "
        "stop:0 #EDF0D8, stop:1 #CFE3FF); "
        "}"
        f"#notebookContainer {{ background-color: {notebook_container_style}; }}"
        f"#settingContainer {{ background-color: {notebook_container_style}; }}"
        f"#quizContainer {{ background-color: {notebook_container_style}; }}"
    )
    question_setting = QuestionSetting()
    question_setting.setObjectName("settingContainer")
    output_area = OutputArea()
    output_area.setObjectName("quizContainer")
    output_area.setStyleSheet(
        "#quizContainer { "
        "background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, "
        "stop:0 #EDF0D8, stop:1 #CFE3FF); "
        "}"
    )
    output_area.setWindowTitle("READY - Generated Questions")
    output_area.resize(900, 700)
    if window_icon is not None:
        output_area.setWindowIcon(window_icon)
    sidebar_notebook = SideBarNotebook()
    sidebar_notebook.setObjectName("notebookContainer")

    database = NotebookDatabase()
    generator_holder = {"instance": None}
    selected_notebook_id = {"value": None}
    selected_notebook_name = {"value": "New Notebook"}

    def refresh_sidebar():
        notebooks = database.list_notebooks()
        sidebar_notebook.set_notebooks(notebooks)

    def refresh_notebook_status(set_count=None):
        if set_count is not None:
            current_count = int(set_count)
        elif selected_notebook_id["value"] is None:
            current_count = output_area.get_set_count(include_empty=False)
        else:
            current_count = output_area.get_set_count(include_empty=True)
        question_setting.update_notebook_status(selected_notebook_name["value"], current_count)

    def handle_generate(payload):
        input_text = payload.get("input_content", "").strip()
        if not input_text:
            QMessageBox.critical(
                notebook,
                "Error!",
                "No readable input content found.\nUse text input or a .txt file.",
                buttons=QMessageBox.Ignore,
                defaultButton=QMessageBox.Ignore,
            )
            return

        quantities = {
            "multiple_choice": payload.get("multiple_choice_qty", 0),
            "true_or_false": payload.get("true_or_false_qty", 0),
            "identification": payload.get("identification_qty", 0),
            "essay": payload.get("essay_qty", 0),
        }

        question_types = {
            "multiple_choice": payload.get("multiple_choice_bool", False),
            "true_or_false": payload.get("true_or_false_bool", False),
            "identification": payload.get("identification_bool", False),
            "essay": payload.get("essay_bool", False),
        }

        try:
            if generator_holder["instance"] is None:
                generator_holder["instance"] = QuestionGenerator()

            generated_output = generator_holder["instance"].generate_questions(
                input_text,
                question_types,
                quantities,
                payload.get("language", "English"),
                use_story_compression=True,
            )
            output_area.set_output_text(generated_output)
            refresh_notebook_status()
        except Exception as error:
            QMessageBox.critical(
                notebook,
                "Generation Error",
                f"Failed to generate questions.\n{error}",
                buttons=QMessageBox.Ignore,
                defaultButton=QMessageBox.Ignore,
            )

    def handle_save(payload):
        generated_output = output_area.get_output_text()
        if not generated_output:
            QMessageBox.critical(
                notebook,
                "Error!",
                "No generated questions found.\nPlease click Generate Question before saving.",
                buttons=QMessageBox.Ignore,
                defaultButton=QMessageBox.Ignore,
            )
            return

        try:
            if selected_notebook_id["value"] is not None:
                save_result = database.save_set_to_notebook(selected_notebook_id["value"], payload, generated_output)
                if not save_result:
                    raise ValueError("Selected notebook no longer exists")
                notebook_data = database.get_notebook_sets(save_result["notebook_id"])
                notebook_name = notebook_data["notebook_name"] if notebook_data else "Notebook"
            else:
                notebook_name = question_setting.ask_notebook_name()
                if not notebook_name:
                    return
                save_result = database.save_notebook(notebook_name, payload, generated_output)

            notebook_id = save_result["notebook_id"]
            set_name = save_result["set_name"]

            refresh_sidebar()

            data = database.get_notebook_sets(notebook_id)
            if data:
                selected_notebook_id["value"] = notebook_id
                selected_notebook_name["value"] = notebook_name
                output_area.load_sets(data.get("sets", []))
                output_area.set_active_set(set_name)
                sidebar_notebook.set_new_notebook_mode(False, notebook_name)
                refresh_notebook_status(len(data.get("sets", [])))

            QMessageBox.information(notebook, "Saved", f"{set_name} saved to notebook '{notebook_name}'.")
        except Exception as error:
            QMessageBox.critical(
                notebook,
                "Save Error",
                f"Failed to save notebook.\n{error}",
                buttons=QMessageBox.Ignore,
                defaultButton=QMessageBox.Ignore,
            )

    def handle_notebook_selected(notebook_id):
        data = database.get_notebook_sets(notebook_id)
        if not data or not data.get("sets"):
            QMessageBox.critical(
                notebook,
                "Load Error",
                "Notebook data could not be loaded.",
                buttons=QMessageBox.Ignore,
                defaultButton=QMessageBox.Ignore,
            )
            return

        question_setting.set_context_hidden(False)
        selected_notebook_id["value"] = notebook_id
        selected_notebook_name["value"] = data.get("notebook_name", "Saved Notebook")
        output_area.load_sets(data["sets"])
        question_setting.set_from_saved_settings(data["sets"][0]["settings"])
        sidebar_notebook.set_new_notebook_mode(False, data.get("notebook_name", ""))
        refresh_notebook_status(len(data.get("sets", [])))

    def handle_new_notebook_requested():
        question_setting.set_context_hidden(False)
        selected_notebook_id["value"] = None
        selected_notebook_name["value"] = "New Notebook"
        output_area.clear_sets()
        output_area.add_set("Set 1", "")
        question_setting.reset_to_defaults()
        sidebar_notebook.set_new_notebook_mode(True)
        refresh_notebook_status()
        QMessageBox.information(
            notebook,
            "New Notebook",
            "Workspace reset for a new notebook. Saved notebooks were not changed.",
        )

    def handle_view_generated_requested():
        if not output_area.get_output_text().strip():
            QMessageBox.information(
                notebook,
                "No Generated Questions",
                "Generate questions first before opening Generated Questions.",
            )
            return

        output_area.show()
        output_area.raise_()
        output_area.activateWindow()

    def handle_output_set_changed(set_payload):
        settings = set_payload.get("settings", {})
        if settings:
            question_setting.set_from_saved_settings(settings)

    def handle_output_set_delete(set_payload):
        button = QMessageBox.question(
            notebook,
            "Delete Set",
            "Are you sure you want to delete this set?",
            buttons=QMessageBox.Yes | QMessageBox.No,
            defaultButton=QMessageBox.No,
        )
        if button != QMessageBox.Yes:
            return

        set_id = set_payload.get("set_id")
        tab_index = int(set_payload.get("_tab_index", -1))

        if set_id:
            result = database.delete_notebook_set(int(set_id))
            if not result.get("deleted"):
                reason = result.get("reason", "unknown")
                if reason == "last_set":
                    QMessageBox.critical(
                        notebook,
                        "Delete Error",
                        "You cannot delete the last set in a notebook.",
                        buttons=QMessageBox.Ignore,
                        defaultButton=QMessageBox.Ignore,
                    )
                    return

                QMessageBox.critical(
                    notebook,
                    "Delete Error",
                    "Set could not be deleted.",
                    buttons=QMessageBox.Ignore,
                    defaultButton=QMessageBox.Ignore,
                )
                return

            notebook_id = result.get("notebook_id")
            if notebook_id:
                selected_notebook_id["value"] = notebook_id
                data = database.get_notebook_sets(notebook_id)
                if data and data.get("sets"):
                    selected_notebook_name["value"] = data.get("notebook_name", selected_notebook_name["value"])
                    output_area.load_sets(data["sets"])
                    question_setting.set_from_saved_settings(data["sets"][0].get("settings", {}))
                    refresh_notebook_status(len(data.get("sets", [])))
                else:
                    output_area.clear_sets()
                    output_area.add_set("Set 1", "")
                    refresh_notebook_status()

            refresh_sidebar()
            QMessageBox.information(notebook, "Deleted", "Set deleted successfully.")
            return

        output_area.remove_set_at(tab_index)
        refresh_notebook_status(output_area.tab_widget.count())
        QMessageBox.information(notebook, "Deleted", "Set deleted successfully.")

    def handle_notebook_delete(notebook_id):
        button = QMessageBox.question(
            notebook,
            "Delete Notebook",
            "Are you sure you want to delete this notebook?",
            buttons=QMessageBox.Yes | QMessageBox.No,
            defaultButton=QMessageBox.No,
        )
        if button != QMessageBox.Yes:
            return

        deleted = database.delete_notebook(notebook_id)
        if not deleted:
            QMessageBox.critical(
                notebook,
                "Delete Error",
                "Notebook could not be deleted.",
                buttons=QMessageBox.Ignore,
                defaultButton=QMessageBox.Ignore,
            )
            return

        refresh_sidebar()
        if selected_notebook_id["value"] == notebook_id:
            question_setting.set_context_hidden(False)
            selected_notebook_id["value"] = None
            selected_notebook_name["value"] = "New Notebook"
            output_area.clear_sets()
            output_area.add_set("Set 1", "")
            question_setting.reset_to_defaults()
            sidebar_notebook.set_new_notebook_mode(True)
            refresh_notebook_status()
        QMessageBox.information(notebook, "Deleted", "Notebook deleted successfully.")

    def handle_notebook_rename(notebook_id):
        notebook_name = question_setting.ask_notebook_name()
        if not notebook_name:
            return

        renamed = database.rename_notebook(notebook_id, notebook_name)
        if not renamed:
            QMessageBox.critical(
                notebook,
                "Rename Error",
                "Notebook could not be renamed.",
                buttons=QMessageBox.Ignore,
                defaultButton=QMessageBox.Ignore,
            )
            return

        refresh_sidebar()
        if selected_notebook_id["value"] == notebook_id:
            selected_notebook_name["value"] = notebook_name
            refresh_notebook_status()
        QMessageBox.information(notebook, "Renamed", "Notebook renamed successfully.")

    question_setting.generate_requested.connect(handle_generate)
    question_setting.save_notebook_requested.connect(handle_save)
    question_setting.view_generated_requested.connect(handle_view_generated_requested)
    output_area.set_changed.connect(handle_output_set_changed)
    output_area.set_delete_requested.connect(handle_output_set_delete)
    output_area.quiz_started.connect(lambda: question_setting.set_context_hidden(True))
    output_area.quiz_revealed.connect(lambda: question_setting.set_context_hidden(False))
    sidebar_notebook.notebook_selected.connect(handle_notebook_selected)
    sidebar_notebook.notebook_new_requested.connect(handle_new_notebook_requested)
    sidebar_notebook.notebook_save_requested.connect(question_setting.request_save)
    sidebar_notebook.notebook_delete_requested.connect(handle_notebook_delete)
    sidebar_notebook.notebook_rename_requested.connect(handle_notebook_rename)

    question_input_layout = QVBoxLayout()
    question_input_layout.addWidget(question_setting)

    sidebar_notebook_layout = QVBoxLayout()
    sidebar_notebook_layout.addWidget(sidebar_notebook)

    notebook_layout = QHBoxLayout()
    notebook_layout.addLayout(sidebar_notebook_layout)
    notebook_layout.addLayout(question_input_layout)

    notebook.setLayout(notebook_layout)

    refresh_sidebar()
    refresh_notebook_status()

    window = notebook
    splash = SplashScreen()

    def show_main_window():
        window.show()

    splash.finished.connect(show_main_window)
    splash.show()
    app.exec()
