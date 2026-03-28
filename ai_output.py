from typing import Dict, List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSizePolicy,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class QuestionCard(QFrame):
    def __init__(self, number: int, item: Dict):
        super().__init__()

        self.item = item
        self.question_type = item.get("question_type", "essay")
        self._button_group: Optional[QButtonGroup] = None
        self._answer_label = QLabel()
        self._answer_label.setVisible(False)
        self._score_label = QLabel()
        self._score_label.setVisible(False)

        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("padding: 8px;")

        container = QVBoxLayout()
        container.setSpacing(8)

        type_label = QLabel(self._get_readable_question_type(self.question_type))
        type_label.setStyleSheet(
            "font-size: 12px; font-weight: 600; padding: 3px 8px; border: 1px solid #777; border-radius: 8px;"
        )
        type_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self._score_label.setStyleSheet("font-size: 13px; font-weight: 600;")

        header_row = QHBoxLayout()
        header_row.addWidget(type_label, alignment=Qt.AlignLeft)
        header_row.addStretch()
        header_row.addWidget(self._score_label, alignment=Qt.AlignRight)
        container.addLayout(header_row)

        question_label = QLabel(f"{number}. {item.get('question', '')}")
        question_label.setWordWrap(True)
        question_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        question_label.setStyleSheet("font-size: 14px; font-weight: 500;")
        container.addWidget(question_label)

        self._answer_widgets: List[QWidget] = []
        self._build_answer_input(container)

        answer_text = (item.get("answer") or "").strip()
        if answer_text and self.question_type != "essay":
            self._answer_label.setText(f"Answer: {answer_text}")
            self._answer_label.setStyleSheet("font-size: 13px;")
            container.addWidget(self._answer_label)

        self.setLayout(container)

    def _build_answer_input(self, container: QVBoxLayout):
        question_type = self.question_type
        choices = self.item.get("choices", [])

        if question_type == "multiple_choice":
            self._button_group = QButtonGroup(self)
            for choice in choices:
                button = QRadioButton(choice)
                button.setStyleSheet("font-size: 13px;")
                self._button_group.addButton(button)
                container.addWidget(button)
                self._answer_widgets.append(button)
            if not choices:
                placeholder = QLabel("No choices available for this question.")
                placeholder.setStyleSheet("font-size: 13px;")
                container.addWidget(placeholder)
            return

        if question_type == "true_or_false":
            self._button_group = QButtonGroup(self)
            for choice in ("True", "False"):
                button = QRadioButton(choice)
                button.setStyleSheet("font-size: 13px;")
                self._button_group.addButton(button)
                container.addWidget(button)
                self._answer_widgets.append(button)
            return

        if question_type == "identification":
            answer_input = QLineEdit()
            answer_input.setPlaceholderText("Type your answer here")
            answer_input.setStyleSheet("font-size: 13px; padding: 6px;")
            container.addWidget(answer_input)
            self._answer_widgets.append(answer_input)
            return

        essay_input = QPlainTextEdit()
        essay_input.setPlaceholderText("Write your essay answer here")
        essay_input.setMinimumHeight(110)
        essay_input.setStyleSheet("font-size: 13px; padding: 6px;")
        container.addWidget(essay_input)
        self._answer_widgets.append(essay_input)

    def _get_readable_question_type(self, question_type: str) -> str:
        labels = {
            "multiple_choice": "Multiple Choice",
            "true_or_false": "True or False",
            "identification": "Identification",
            "essay": "Essay",
        }
        return f"Type: {labels.get(question_type, 'Essay')}"

    def set_take_quiz_mode(self):
        self._reset_answer_inputs()
        self._answer_label.setVisible(False)
        self._score_label.setVisible(False)
        for widget in self._answer_widgets:
            widget.setEnabled(True)

    def _reset_answer_inputs(self):
        if self._button_group is not None:
            self._button_group.setExclusive(False)
            for button in self._button_group.buttons():
                button.setChecked(False)
            self._button_group.setExclusive(True)

        for widget in self._answer_widgets:
            if isinstance(widget, QLineEdit):
                widget.clear()
            elif isinstance(widget, QPlainTextEdit):
                widget.clear()

    def set_locked_mode(self):
        self._answer_label.setVisible(False)
        self._score_label.setVisible(False)
        for widget in self._answer_widgets:
            widget.setEnabled(False)

    def set_show_answers_mode(self):
        self._select_correct_answer_option()
        self._answer_label.setVisible(bool(self._answer_label.text()))
        for widget in self._answer_widgets:
            widget.setEnabled(False)

    def _select_correct_answer_option(self):
        if self._button_group is None:
            return

        correct_answer = str(self.item.get("answer", "")).strip()
        if not correct_answer:
            return

        normalized_answer = correct_answer.strip().lower()

        if self.question_type == "true_or_false":
            if normalized_answer == "tama":
                normalized_answer = "true"
            if normalized_answer == "mali":
                normalized_answer = "false"

            for button in self._button_group.buttons():
                if button.text().strip().lower() == normalized_answer:
                    button.setChecked(True)
                    return
            return

        if self.question_type != "multiple_choice":
            return

        answer_label = correct_answer.strip().upper()
        if len(answer_label) == 1 and answer_label in {"A", "B", "C", "D"}:
            for button in self._button_group.buttons():
                button_label = button.text().split(")", 1)[0].strip().upper()
                if button_label == answer_label:
                    button.setChecked(True)
                    return
            return

        for button in self._button_group.buttons():
            if button.text().strip().lower() == normalized_answer:
                button.setChecked(True)
                return

    def set_scoring_result(self, earned: int, total: int):
        if self.question_type not in {"multiple_choice", "true_or_false"}:
            return

        self._score_label.setText(f"{earned}/{total}")
        if earned == total:
            self._score_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #8fd19e;")
        else:
            self._score_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #ff9f9f;")
        self._score_label.setVisible(True)

    def clear_scoring_result(self):
        self._score_label.clear()
        self._score_label.setVisible(False)

    def evaluate_score(self) -> tuple[bool, int, int]:
        if self.question_type not in {"multiple_choice", "true_or_false"}:
            return False, 0, 0

        correct_answer = str(self.item.get("answer", "")).strip()
        selected_value = self._get_selected_value()
        earned = 0

        if self.question_type == "multiple_choice":
            selected_label = selected_value.split(")", 1)[0].strip().upper() if selected_value else ""
            correct_label = correct_answer.strip().upper()

            if len(correct_label) == 1 and correct_label in {"A", "B", "C", "D"}:
                earned = 1 if selected_label == correct_label else 0
            else:
                earned = 1 if selected_value.strip().lower() == correct_answer.lower() else 0

        if self.question_type == "true_or_false":
            earned = 1 if selected_value.strip().lower() == correct_answer.lower() else 0

        return True, earned, 1

    def _get_selected_value(self) -> str:
        if self._button_group is None:
            return ""
        selected = self._button_group.checkedButton()
        if selected is None:
            return ""
        return selected.text().strip()


class QuizCanvas(QWidget):
    delete_requested = Signal()
    quiz_started = Signal()
    quiz_revealed = Signal()

    def __init__(self, generated_output: str, questions: List[Dict]):
        super().__init__()

        self.generated_output = generated_output
        self.questions = questions
        self._cards: List[QuestionCard] = []

        self.take_quiz_button = QPushButton("Take the Quiz")
        self.show_answers_button = QPushButton("Show Answers")
        self.score_label = QLabel("Score: -")
        self.take_quiz_button.setStyleSheet("padding: 8px; font-size: 14px;")
        self.show_answers_button.setStyleSheet("padding: 8px; font-size: 14px;")
        self.score_label.setStyleSheet("font-size: 14px; font-weight: 600;")

        top_bar = QHBoxLayout()
        top_bar.addWidget(self.take_quiz_button)
        top_bar.addWidget(self.show_answers_button)
        top_bar.addStretch()
        top_bar.addWidget(self.score_label)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout()
        self.content_layout.setAlignment(Qt.AlignTop)
        self.content_widget.setLayout(self.content_layout)
        self.scroll_area.setWidget(self.content_widget)

        layout = QVBoxLayout()
        layout.addLayout(top_bar)
        layout.addWidget(self.scroll_area)
        self.setLayout(layout)

        self.take_quiz_button.clicked.connect(self._on_take_quiz_clicked)
        self.show_answers_button.clicked.connect(self._on_show_answers_clicked)

        self.refresh(generated_output, questions)

    def refresh(self, generated_output: str, questions: List[Dict]):
        self.generated_output = generated_output or ""
        self.questions = questions or []

        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self._cards = []
        self.score_label.setText("Score: -")

        if not self.questions:
            fallback_editor = QTextEdit()
            fallback_editor.setReadOnly(True)
            fallback_editor.setPlainText(self.generated_output)
            fallback_editor.setMinimumHeight(600)
            fallback_editor.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.content_layout.addWidget(fallback_editor)
            return

        for index, item in enumerate(self.questions, start=1):
            card = QuestionCard(index, item)
            self.content_layout.addWidget(card)
            self._cards.append(card)

        self.finish_button = QPushButton("Finish")
        self.finish_button.setStyleSheet(
            "QPushButton { padding: 8px; font-size: 14px; background-color: #d32f2f; color: white; }"
            "QPushButton:hover { background-color: #b71c1c; color: white; }"
            "QPushButton:pressed { background-color: #8e0000; color: white; }"
        )
        self.finish_button.clicked.connect(self._on_finish_clicked)

        self.delete_set_button = QPushButton("Delete Set")
        self.delete_set_button.setStyleSheet("padding: 8px; font-size: 14px;")
        self.delete_set_button.clicked.connect(self._request_delete)

        action_row = QHBoxLayout()
        action_row.addWidget(self.finish_button, alignment=Qt.AlignLeft)
        action_row.addStretch()
        action_row.addWidget(self.delete_set_button, alignment=Qt.AlignRight)
        self.content_layout.addLayout(action_row)

        self.content_layout.addStretch()
        self.set_locked_mode()

    def set_locked_mode(self):
        for card in self._cards:
            card.set_locked_mode()
            card.clear_scoring_result()
        if hasattr(self, "finish_button"):
            self.finish_button.setEnabled(False)

    def set_take_quiz_mode(self):
        for card in self._cards:
            card.set_take_quiz_mode()
            card.clear_scoring_result()
        if hasattr(self, "finish_button"):
            self.finish_button.setEnabled(True)
        self.score_label.setText("Score: -")

    def set_show_answers_mode(self):
        for card in self._cards:
            card.set_show_answers_mode()

    def _on_take_quiz_clicked(self):
        self.set_take_quiz_mode()
        self.quiz_started.emit()

    def _on_show_answers_clicked(self):
        self.set_show_answers_mode()
        self.quiz_revealed.emit()

    def finish_quiz(self):
        earned_total = 0
        max_total = 0

        for card in self._cards:
            scored, earned, total = card.evaluate_score()
            if not scored:
                continue

            earned_total += earned
            max_total += total
            card.set_scoring_result(earned, total)

        if max_total == 0:
            self.score_label.setText("Score: -")
            return

        self.score_label.setText(f"Score: {earned_total}/{max_total}")

    def _on_finish_clicked(self):
        self.finish_quiz()
        self.quiz_revealed.emit()

    def _request_delete(self):
        self.delete_requested.emit()


class OutputArea(QWidget):
    set_changed = Signal(dict)
    set_delete_requested = Signal(dict)
    quiz_started = Signal()
    quiz_revealed = Signal()

    def __init__(self):
        super().__init__()

        self.tab_widget = QTabWidget()
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        self._set_payloads = []
        self._set_views: List[QuizCanvas] = []
        self._loading_sets = False

        layout = QVBoxLayout()
        layout.addWidget(self.tab_widget)
        self.setLayout(layout)

        self.add_set("Set 1", "")

    def _create_set_view(self, generated_output: str, questions: List[Dict]):
        view = QuizCanvas(generated_output, questions)
        view.delete_requested.connect(lambda: self._on_view_delete_requested(view))
        view.quiz_started.connect(self.quiz_started.emit)
        view.quiz_revealed.connect(self.quiz_revealed.emit)
        view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        view.setMinimumSize(600, 600)
        return view

    def add_set(self, set_name: str, generated_output: str, payload: dict | None = None):
        resolved_payload = dict(payload or {})
        resolved_payload.setdefault("set_name", set_name)
        resolved_payload.setdefault("generated_output", generated_output)
        resolved_payload.setdefault("settings", {})
        resolved_payload.setdefault("questions", self._parse_generated_output(generated_output))

        view = self._create_set_view(resolved_payload.get("generated_output", ""), resolved_payload.get("questions", []))
        self.tab_widget.addTab(view, set_name)
        self._set_views.append(view)
        self._set_payloads.append(resolved_payload)

    def clear_sets(self):
        self.tab_widget.clear()
        self._set_payloads = []
        self._set_views = []

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

        index = self.tab_widget.currentIndex()
        if 0 <= index < len(self._set_payloads):
            self._set_payloads[index]["generated_output"] = text
            self._set_payloads[index]["questions"] = self._parse_generated_output(text)

        if 0 <= index < len(self._set_views):
            view = self._set_views[index]
            payload = self._set_payloads[index]
            view.refresh(payload.get("generated_output", ""), payload.get("questions", []))

    def get_output_text(self) -> str:
        index = self.tab_widget.currentIndex()
        if 0 <= index < len(self._set_payloads):
            return str(self._set_payloads[index].get("generated_output", "")).strip()
        return ""

    def get_current_set_payload(self):
        index = self.tab_widget.currentIndex()
        if 0 <= index < len(self._set_payloads):
            return self._set_payloads[index]
        return None

    def get_set_count(self, include_empty: bool = True) -> int:
        if include_empty:
            return len(self._set_payloads)

        count = 0
        for payload in self._set_payloads:
            generated_output = str(payload.get("generated_output", "")).strip()
            if generated_output:
                count += 1
        return count

    def _on_tab_changed(self, index: int):
        if self._loading_sets:
            return

        if 0 <= index < len(self._set_payloads):
            self.set_changed.emit(self._set_payloads[index])

    def remove_set_at(self, index: int):
        if not (0 <= index < len(self._set_payloads)):
            return

        self.tab_widget.removeTab(index)
        self._set_payloads.pop(index)
        self._set_views.pop(index)

        if not self._set_payloads:
            self.add_set("Set 1", "")

        current_payload = self.get_current_set_payload()
        if current_payload is not None:
            self.set_changed.emit(current_payload)

    def _on_view_delete_requested(self, view: QuizCanvas):
        tab_index = self.tab_widget.indexOf(view)
        if tab_index < 0 or tab_index >= len(self._set_payloads):
            return

        payload = dict(self._set_payloads[tab_index])
        payload["_tab_index"] = tab_index
        self.set_delete_requested.emit(payload)

    def _parse_generated_output(self, generated_output: str) -> List[Dict]:
        blocks = [block.strip() for block in generated_output.split("\n\n") if block.strip()]
        parsed_items: List[Dict] = []

        for block in blocks:
            lines = [line.strip() for line in block.splitlines() if line.strip()]
            if not lines:
                continue

            question_line = lines[0]
            if ". " in question_line:
                question_text = question_line.split(". ", 1)[1].strip()
            else:
                question_text = question_line

            lowered_question_text = question_text.lower()
            legacy_tf_prefix = "true or false:"
            if lowered_question_text.startswith(legacy_tf_prefix):
                question_text = question_text[len(legacy_tf_prefix):].strip()

            choices = [line for line in lines if line.startswith(("A)", "B)", "C)", "D)"))]
            answer_line = ""
            for line in lines:
                if line.lower().startswith("answer:"):
                    answer_line = line.split(":", 1)[1].strip()

            normalized_answer = answer_line.strip().lower()
            is_true_false_answer = normalized_answer in {"true", "false", "tama", "mali"}

            question_type = "essay"
            if choices:
                question_type = "multiple_choice"
            elif is_true_false_answer:
                question_type = "true_or_false"
            elif answer_line:
                question_type = "identification"

            if question_type == "essay":
                answer_line = ""

            parsed_items.append(
                {
                    "question_type": question_type,
                    "question": question_text,
                    "choices": choices,
                    "answer": answer_line,
                }
            )

        return parsed_items
