import sys

from PySide6.QtWidgets import QApplication, QHBoxLayout, QMessageBox, QVBoxLayout, QWidget

from ai_output import OutputArea
from database import NotebookDatabase
from question_generator import QuestionGenerator
from question_setting import QuestionSetting, SideBarNotebook


if __name__ == "__main__":
    app = QApplication(sys.argv)

    notebook = QWidget()
    question_setting = QuestionSetting()
    output_area = OutputArea()
    sidebar_notebook = SideBarNotebook()

    database = NotebookDatabase()
    generator_holder = {"instance": None}
    selected_notebook_id = {"value": None}

    def refresh_sidebar():
        notebooks = database.list_notebooks()
        sidebar_notebook.set_notebooks(notebooks)

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
            )
            output_area.set_output_text(generated_output)
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
                output_area.load_sets(data.get("sets", []))
                output_area.set_active_set(set_name)
                sidebar_notebook.set_new_notebook_mode(False, notebook_name)

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

        selected_notebook_id["value"] = notebook_id
        output_area.load_sets(data["sets"])
        question_setting.set_from_saved_settings(data["sets"][0]["settings"])
        sidebar_notebook.set_new_notebook_mode(False, data.get("notebook_name", ""))

    def handle_new_notebook_requested():
        selected_notebook_id["value"] = None
        output_area.clear_sets()
        output_area.add_set("Set 1", "")
        question_setting.reset_to_defaults()
        sidebar_notebook.set_new_notebook_mode(True)
        QMessageBox.information(
            notebook,
            "New Notebook",
            "Workspace reset for a new notebook. Saved notebooks were not changed.",
        )

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
                    output_area.load_sets(data["sets"])
                    question_setting.set_from_saved_settings(data["sets"][0].get("settings", {}))
                else:
                    output_area.clear_sets()
                    output_area.add_set("Set 1", "")

            refresh_sidebar()
            QMessageBox.information(notebook, "Deleted", "Set deleted successfully.")
            return

        output_area.remove_set_at(tab_index)
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
            selected_notebook_id["value"] = None
            output_area.clear_sets()
            output_area.add_set("Set 1", "")
            question_setting.reset_to_defaults()
            sidebar_notebook.set_new_notebook_mode(True)
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
        QMessageBox.information(notebook, "Renamed", "Notebook renamed successfully.")

    question_setting.generate_requested.connect(handle_generate)
    question_setting.save_notebook_requested.connect(handle_save)
    output_area.set_changed.connect(handle_output_set_changed)
    output_area.set_delete_requested.connect(handle_output_set_delete)
    sidebar_notebook.notebook_selected.connect(handle_notebook_selected)
    sidebar_notebook.notebook_new_requested.connect(handle_new_notebook_requested)
    sidebar_notebook.notebook_delete_requested.connect(handle_notebook_delete)
    sidebar_notebook.notebook_rename_requested.connect(handle_notebook_rename)

    question_input_layout = QVBoxLayout()
    question_input_layout.addWidget(question_setting)

    ai_output_layout = QVBoxLayout()
    ai_output_layout.addWidget(output_area)

    sidebar_notebook_layout = QVBoxLayout()
    sidebar_notebook_layout.addWidget(sidebar_notebook)

    notebook_layout = QHBoxLayout()
    notebook_layout.addLayout(sidebar_notebook_layout)
    notebook_layout.addLayout(question_input_layout)
    notebook_layout.addLayout(ai_output_layout)

    notebook.setLayout(notebook_layout)

    refresh_sidebar()

    window = notebook
    window.show()
    app.exec()
