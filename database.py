import json
import sqlite3
from typing import Dict, List, Optional


class NotebookDatabase:
    def __init__(self, database_path: str = "notebook.db"):
        self.database_path = database_path
        self._initialize_database()

    def _connect(self):
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize_database(self):
        create_tables = [
            """
            CREATE TABLE IF NOT EXISTS question_setting (
                id INTEGER PRIMARY KEY,
                file_input BLOB NULL,
                text_input TEXT NULL,
                multiple_choice_bool INTEGER NOT NULL CHECK (multiple_choice_bool IN (0, 1)),
                true_or_false_bool INTEGER NOT NULL CHECK (true_or_false_bool IN (0, 1)),
                identification_bool INTEGER NOT NULL CHECK (identification_bool IN (0, 1)),
                essay_bool INTEGER NOT NULL CHECK (essay_bool IN (0, 1)),
                multiple_choice_qty INTEGER NOT NULL,
                true_or_false_qty INTEGER NOT NULL,
                identification_qty INTEGER NOT NULL,
                essay_qty INTEGER NOT NULL,
                language TEXT NOT NULL CHECK (language IN ('English', 'Filipino'))
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS quiz (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS quiz_question (
                id INTEGER PRIMARY KEY,
                quiz_id INTEGER,
                question_type TEXT NOT NULL,
                content TEXT NOT NULL,
                FOREIGN KEY (quiz_id) REFERENCES quiz(id) ON DELETE CASCADE
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS quiz_answer (
                id INTEGER PRIMARY KEY,
                quiz_id INTEGER,
                question_id INTEGER,
                quiz_question_answer_choice TEXT NOT NULL,
                quiz_question_answer_correct TEXT NOT NULL,
                FOREIGN KEY (quiz_id) REFERENCES quiz(id) ON DELETE CASCADE,
                FOREIGN KEY (question_id) REFERENCES quiz_question(id) ON DELETE CASCADE
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS notebook (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                question_setting_id INTEGER,
                quiz_id INTEGER,
                FOREIGN KEY (question_setting_id) REFERENCES question_setting(id) ON DELETE SET NULL,
                FOREIGN KEY (quiz_id) REFERENCES quiz(id) ON DELETE SET NULL
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS notebook_set (
                id INTEGER PRIMARY KEY,
                notebook_id INTEGER NOT NULL,
                set_index INTEGER NOT NULL,
                set_name TEXT NOT NULL,
                question_setting_id INTEGER NOT NULL,
                quiz_id INTEGER NOT NULL,
                FOREIGN KEY (notebook_id) REFERENCES notebook(id) ON DELETE CASCADE,
                FOREIGN KEY (question_setting_id) REFERENCES question_setting(id) ON DELETE CASCADE,
                FOREIGN KEY (quiz_id) REFERENCES quiz(id) ON DELETE CASCADE,
                UNIQUE(notebook_id, set_index)
            );
            """,
        ]

        with self._connect() as conn:
            cursor = conn.cursor()
            for statement in create_tables:
                cursor.execute(statement)
            conn.commit()

    def save_notebook(self, name: str, settings: Dict, generated_output: str) -> Dict:
        notebook_name = name.strip()
        if not notebook_name:
            raise ValueError("Notebook name is required")

        with self._connect() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM notebook WHERE lower(name) = lower(?)", (notebook_name,))
            notebook_row = cursor.fetchone()
            if notebook_row:
                notebook_id = notebook_row["id"]
                self._ensure_notebook_sets_initialized(conn, notebook_id)
            else:
                cursor.execute(
                    "INSERT INTO notebook (name, question_setting_id, quiz_id) VALUES (?, NULL, NULL)",
                    (notebook_name,),
                )
                notebook_id = cursor.lastrowid

            cursor.execute(
                "SELECT COALESCE(MAX(set_index), 0) + 1 AS next_index FROM notebook_set WHERE notebook_id = ?",
                (notebook_id,),
            )
            next_set_index = int(cursor.fetchone()["next_index"])
            set_name = f"Set {next_set_index}"

            question_setting_id = self._insert_question_setting(cursor, settings)
            quiz_id = self._insert_quiz(cursor, notebook_name, set_name, generated_output)

            cursor.execute(
                """
                INSERT INTO notebook_set (notebook_id, set_index, set_name, question_setting_id, quiz_id)
                VALUES (?, ?, ?, ?, ?)
                """,
                (notebook_id, next_set_index, set_name, question_setting_id, quiz_id),
            )

            cursor.execute("SELECT question_setting_id, quiz_id FROM notebook WHERE id = ?", (notebook_id,))
            notebook_meta = cursor.fetchone()
            if notebook_meta and (notebook_meta["question_setting_id"] is None or notebook_meta["quiz_id"] is None):
                cursor.execute(
                    "UPDATE notebook SET question_setting_id = ?, quiz_id = ? WHERE id = ?",
                    (question_setting_id, quiz_id, notebook_id),
                )

            conn.commit()
            return {"notebook_id": notebook_id, "set_name": set_name}

    def save_set_to_notebook(self, notebook_id: int, settings: Dict, generated_output: str) -> Optional[Dict]:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM notebook WHERE id = ?", (notebook_id,))
            notebook_row = cursor.fetchone()
            if not notebook_row:
                return None

            self._ensure_notebook_sets_initialized(conn, notebook_id)

            notebook_name = notebook_row["name"]
            cursor.execute(
                "SELECT COALESCE(MAX(set_index), 0) + 1 AS next_index FROM notebook_set WHERE notebook_id = ?",
                (notebook_id,),
            )
            next_set_index = int(cursor.fetchone()["next_index"])
            set_name = f"Set {next_set_index}"

            question_setting_id = self._insert_question_setting(cursor, settings)
            quiz_id = self._insert_quiz(cursor, notebook_name, set_name, generated_output)

            cursor.execute(
                """
                INSERT INTO notebook_set (notebook_id, set_index, set_name, question_setting_id, quiz_id)
                VALUES (?, ?, ?, ?, ?)
                """,
                (notebook_id, next_set_index, set_name, question_setting_id, quiz_id),
            )

            conn.commit()
            return {"notebook_id": notebook_id, "set_name": set_name}

    def _insert_question_setting(self, cursor, settings: Dict) -> int:
        cursor.execute(
            """
            INSERT INTO question_setting (
                file_input,
                text_input,
                multiple_choice_bool,
                true_or_false_bool,
                identification_bool,
                essay_bool,
                multiple_choice_qty,
                true_or_false_qty,
                identification_qty,
                essay_qty,
                language
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                settings.get("file_input", ""),
                settings.get("text_input", ""),
                int(settings.get("multiple_choice_bool", False)),
                int(settings.get("true_or_false_bool", False)),
                int(settings.get("identification_bool", False)),
                int(settings.get("essay_bool", False)),
                int(settings.get("multiple_choice_qty", 0)),
                int(settings.get("true_or_false_qty", 0)),
                int(settings.get("identification_qty", 0)),
                int(settings.get("essay_qty", 0)),
                settings.get("language", "English"),
            ),
        )
        return cursor.lastrowid

    def _insert_quiz(self, cursor, notebook_name: str, set_name: str, generated_output: str) -> int:
        cursor.execute("INSERT INTO quiz (title) VALUES (?)", (f"{notebook_name} - {set_name}",))
        quiz_id = cursor.lastrowid

        parsed_questions = self._parse_generated_output(generated_output)
        for item in parsed_questions:
            cursor.execute(
                "INSERT INTO quiz_question (quiz_id, question_type, content) VALUES (?, ?, ?)",
                (quiz_id, item["question_type"], item["question"]),
            )
            question_id = cursor.lastrowid

            choices_payload = {
                "choices": item.get("choices", []),
                "context": item.get("context", ""),
            }
            cursor.execute(
                """
                INSERT INTO quiz_answer (
                    quiz_id,
                    question_id,
                    quiz_question_answer_choice,
                    quiz_question_answer_correct
                ) VALUES (?, ?, ?, ?)
                """,
                (
                    quiz_id,
                    question_id,
                    json.dumps(choices_payload, ensure_ascii=False),
                    item.get("answer", ""),
                ),
            )

        return quiz_id

    def list_notebooks(self) -> List[Dict]:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM notebook ORDER BY id DESC")
            rows = cursor.fetchall()
            return [{"id": row["id"], "name": row["name"]} for row in rows]

    def delete_notebook(self, notebook_id: int) -> bool:
        with self._connect() as conn:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT question_setting_id, quiz_id FROM notebook_set WHERE notebook_id = ?",
                (notebook_id,),
            )
            set_rows = cursor.fetchall()

            cursor.execute("SELECT question_setting_id, quiz_id FROM notebook WHERE id = ?", (notebook_id,))
            legacy_row = cursor.fetchone()
            if not legacy_row and not set_rows:
                return False

            question_setting_ids = {row["question_setting_id"] for row in set_rows if row["question_setting_id"]}
            quiz_ids = {row["quiz_id"] for row in set_rows if row["quiz_id"]}

            if legacy_row:
                if legacy_row["question_setting_id"]:
                    question_setting_ids.add(legacy_row["question_setting_id"])
                if legacy_row["quiz_id"]:
                    quiz_ids.add(legacy_row["quiz_id"])

            cursor.execute("DELETE FROM notebook WHERE id = ?", (notebook_id,))

            for quiz_id in quiz_ids:
                cursor.execute("DELETE FROM quiz WHERE id = ?", (quiz_id,))
            for question_setting_id in question_setting_ids:
                cursor.execute("DELETE FROM question_setting WHERE id = ?", (question_setting_id,))

            conn.commit()
            return True

    def rename_notebook(self, notebook_id: int, new_name: str) -> bool:
        cleaned_name = new_name.strip()
        if not cleaned_name:
            return False

        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE notebook SET name = ? WHERE id = ?", (cleaned_name, notebook_id))
            notebook_updated = cursor.rowcount > 0
            if not notebook_updated:
                return False

            cursor.execute(
                "SELECT set_index, quiz_id FROM notebook_set WHERE notebook_id = ? ORDER BY set_index ASC",
                (notebook_id,),
            )
            set_rows = cursor.fetchall()
            if set_rows:
                for row in set_rows:
                    cursor.execute(
                        "UPDATE quiz SET title = ? WHERE id = ?",
                        (f"{cleaned_name} - Set {row['set_index']}", row["quiz_id"]),
                    )
            else:
                cursor.execute(
                    "UPDATE quiz SET title = ? WHERE id = (SELECT quiz_id FROM notebook WHERE id = ?)",
                    (cleaned_name, notebook_id),
                )

            conn.commit()
            return True

    def get_notebook_sets(self, notebook_id: int) -> Optional[Dict]:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, question_setting_id, quiz_id FROM notebook WHERE id = ?", (notebook_id,))
            notebook = cursor.fetchone()
            if not notebook:
                return None

            self._ensure_notebook_sets_initialized(conn, notebook_id)

            cursor.execute(
                """
                SELECT id, set_index, set_name, question_setting_id, quiz_id
                FROM notebook_set
                WHERE notebook_id = ?
                ORDER BY set_index ASC
                """,
                (notebook_id,),
            )
            set_rows = cursor.fetchall()

            sets = []
            for set_row in set_rows:
                settings = self._fetch_settings(conn, set_row["question_setting_id"])
                questions = self._fetch_questions(conn, set_row["quiz_id"])
                sets.append(
                    {
                        "set_id": set_row["id"],
                        "set_name": set_row["set_name"],
                        "settings": settings,
                        "questions": questions,
                        "generated_output": self._format_questions_for_display(questions),
                    }
                )

            return {
                "notebook_id": notebook["id"],
                "notebook_name": notebook["name"],
                "sets": sets,
            }

    def _ensure_notebook_sets_initialized(self, conn, notebook_id: int):
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS count FROM notebook_set WHERE notebook_id = ?", (notebook_id,))
        set_count = int(cursor.fetchone()["count"])
        if set_count > 0:
            return

        cursor.execute("SELECT question_setting_id, quiz_id FROM notebook WHERE id = ?", (notebook_id,))
        notebook_row = cursor.fetchone()
        if not notebook_row:
            return

        question_setting_id = notebook_row["question_setting_id"]
        quiz_id = notebook_row["quiz_id"]
        if question_setting_id and quiz_id:
            cursor.execute(
                """
                INSERT INTO notebook_set (notebook_id, set_index, set_name, question_setting_id, quiz_id)
                VALUES (?, 1, 'Set 1', ?, ?)
                """,
                (notebook_id, question_setting_id, quiz_id),
            )

    def get_notebook_data(self, notebook_id: int) -> Optional[Dict]:
        set_data = self.get_notebook_sets(notebook_id)
        if not set_data or not set_data["sets"]:
            return None

        first_set = set_data["sets"][0]
        return {
            "notebook_id": set_data["notebook_id"],
            "notebook_name": set_data["notebook_name"],
            "settings": first_set["settings"],
            "questions": first_set["questions"],
            "generated_output": first_set["generated_output"],
            "sets": set_data["sets"],
        }

    def _fetch_settings(self, conn, question_setting_id: int) -> Dict:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                file_input,
                text_input,
                multiple_choice_bool,
                true_or_false_bool,
                identification_bool,
                essay_bool,
                multiple_choice_qty,
                true_or_false_qty,
                identification_qty,
                essay_qty,
                language
            FROM question_setting
            WHERE id = ?
            """,
            (question_setting_id,),
        )
        row = cursor.fetchone()
        if not row:
            return {
                "file_input": "",
                "text_input": "",
                "multiple_choice_bool": False,
                "true_or_false_bool": False,
                "identification_bool": False,
                "essay_bool": False,
                "multiple_choice_qty": 0,
                "true_or_false_qty": 0,
                "identification_qty": 0,
                "essay_qty": 0,
                "language": "English",
            }

        return {
            "file_input": row["file_input"] or "",
            "text_input": row["text_input"] or "",
            "multiple_choice_bool": bool(row["multiple_choice_bool"]),
            "true_or_false_bool": bool(row["true_or_false_bool"]),
            "identification_bool": bool(row["identification_bool"]),
            "essay_bool": bool(row["essay_bool"]),
            "multiple_choice_qty": int(row["multiple_choice_qty"]),
            "true_or_false_qty": int(row["true_or_false_qty"]),
            "identification_qty": int(row["identification_qty"]),
            "essay_qty": int(row["essay_qty"]),
            "language": row["language"],
        }

    def _fetch_questions(self, conn, quiz_id: int) -> List[Dict]:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT qq.id, qq.question_type, qq.content, qa.quiz_question_answer_choice, qa.quiz_question_answer_correct
            FROM quiz_question qq
            LEFT JOIN quiz_answer qa ON qa.question_id = qq.id
            WHERE qq.quiz_id = ?
            ORDER BY qq.id ASC
            """,
            (quiz_id,),
        )
        rows = cursor.fetchall()

        questions = []
        for row in rows:
            choices = []
            context = ""
            raw_choices = row["quiz_question_answer_choice"]
            if raw_choices:
                try:
                    decoded = json.loads(raw_choices)
                    if isinstance(decoded, list):
                        choices = decoded
                    elif isinstance(decoded, dict):
                        choices = decoded.get("choices", [])
                        context = decoded.get("context", "")
                except json.JSONDecodeError:
                    choices = []

            questions.append(
                {
                    "question_type": row["question_type"],
                    "question": row["content"],
                    "choices": choices,
                    "answer": row["quiz_question_answer_correct"] or "",
                    "context": context,
                }
            )

        return questions

    def _parse_generated_output(self, generated_output: str) -> List[Dict]:
        blocks = [block.strip() for block in generated_output.split("\n\n") if block.strip()]
        parsed_items = []

        for block in blocks:
            lines = [line.strip() for line in block.splitlines() if line.strip()]
            if not lines:
                continue

            question_line = lines[0]
            if ". " in question_line:
                question_text = question_line.split(". ", 1)[1].strip()
            else:
                question_text = question_line

            choices = [line for line in lines if line.startswith(("A)", "B)", "C)", "D)"))]
            answer_line = ""
            context_line = ""
            for line in lines:
                if line.lower().startswith("answer:"):
                    answer_line = line.split(":", 1)[1].strip()
                if line.lower().startswith("context:"):
                    context_line = line.split(":", 1)[1].strip()

            question_type = "essay"
            if choices:
                question_type = "multiple_choice"
            elif question_text.lower().startswith("true or false:"):
                question_type = "true_or_false"
            elif answer_line:
                question_type = "identification"

            parsed_items.append(
                {
                    "question_type": question_type,
                    "question": question_text,
                    "choices": choices,
                    "answer": answer_line,
                    "context": context_line,
                }
            )

        return parsed_items

    def _format_questions_for_display(self, questions: List[Dict]) -> str:
        output_lines = []
        number = 1

        for item in questions:
            output_lines.append(f"{number}. {item['question']}")
            for choice in item.get("choices", []):
                output_lines.append(choice)
            if item.get("answer"):
                output_lines.append(f"Answer: {item['answer']}")
            if item.get("context"):
                output_lines.append(f"Context: {item['context']}")
            output_lines.append("")
            number += 1

        return "\n".join(output_lines).strip()
