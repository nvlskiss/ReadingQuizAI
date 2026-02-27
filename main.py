from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QTabWidget, QTextEdit, QScrollArea, QRadioButton, QButtonGroup, QLabel, QGroupBox, QCheckBox
from PySide6.QtCore import Qt
import sys

from question_setting import QuestionSetting
from file_input import InputArea
from question_generator import QuestionGenerator
from fairytale_qa_handler import FairytaleQAHandler
from quiz_parser import QuizParser


class QuizWindow(QMainWindow):
    """Interactive Quiz Window"""
    def __init__(self, questions, result_windows_list, reference_answers=None, fairytale_handler=None):
        super().__init__()
        self.setWindowTitle("Quiz")
        self.setGeometry(100, 100, 900, 700)
        
        self.questions = questions
        self.reference_answers = reference_answers or []
        self.fairytale_handler = fairytale_handler
        self.user_answers = {}
        self.current_question_index = 0
        self.graded = False
        self.result_windows_list = result_windows_list  # Keep reference to result windows
        
        # Create main widget
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # Question display area
        self.question_label = QLabel()
        self.question_label.setWordWrap(True)
        self.question_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        main_layout.addWidget(self.question_label)
        
        # Answer input area
        self.answer_widget = QWidget()
        self.answer_layout = QVBoxLayout()
        self.answer_widget.setLayout(self.answer_layout)
        main_layout.addWidget(self.answer_widget)
        
        # Navigation buttons
        nav_layout = QHBoxLayout()
        self.prev_button = QPushButton("< Previous")
        self.prev_button.clicked.connect(self.previous_question)
        self.next_button = QPushButton("Next >")
        self.next_button.clicked.connect(self.next_question)
        self.submit_button = QPushButton("Submit Quiz")
        self.submit_button.clicked.connect(self.submit_quiz)
        
        nav_layout.addWidget(self.prev_button)
        nav_layout.addStretch()
        nav_layout.addWidget(self.next_button)
        nav_layout.addWidget(self.submit_button)
        
        self.progress_label = QLabel()
        progress_nav = QHBoxLayout()
        progress_nav.addWidget(self.progress_label)
        progress_nav.addStretch()
        progress_nav.addLayout(nav_layout)
        
        main_layout.addLayout(progress_nav)
        
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        # Display first question
        self.display_question(0)
    
    def display_question(self, index):
        """Display a specific question"""
        if index < 0 or index >= len(self.questions):
            return
        
        self.current_question_index = index
        question = self.questions[index]
        
        # Update progress
        self.progress_label.setText(f"Question {index + 1} of {len(self.questions)}")
        
        # Update question label with better formatting
        question_text = question["question"]
        self.question_label.setText(f"<b>{question_text}</b>")
        self.question_label.setMinimumHeight(60)
        
        # Clear answer layout
        for i in reversed(range(self.answer_layout.count())): 
            widget = self.answer_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        # Add spacing before answer options
        self.answer_layout.addSpacing(20)
        
        # Create answer input based on type
        if question["type"] == "multiple_choice":
            self.create_multiple_choice_input(question)
        elif question["type"] == "true_or_false":
            self.create_true_false_input(question)
        elif question["type"] == "identification":
            self.create_identification_input(question)
        elif question["type"] == "essay":
            self.create_essay_input(question)
        
        # Add stretch at bottom
        self.answer_layout.addStretch()
        
        # Update button states
        self.prev_button.setEnabled(index > 0)
        self.next_button.setEnabled(index < len(self.questions) - 1)
    
    def create_multiple_choice_input(self, question):
        """Create multiple choice radio buttons"""
        group = QButtonGroup()
        for i, option in enumerate(question.get("options", [])):
            radio = QRadioButton(f"{chr(65 + i)}) {option}")
            radio.setStyleSheet("QRadioButton { font-size: 14px; padding: 8px; }")
            group.addButton(radio, i)
            self.answer_layout.addWidget(radio)
            
            # Check saved answer
            if self.current_question_index in self.user_answers:
                saved_index = self.user_answers[self.current_question_index]
                if i == saved_index:
                    radio.setChecked(True)
        
        # Store group reference
        self.current_group = group
        group.buttonClicked.connect(lambda: self.save_answer(group.checkedId()))
    
    def create_true_false_input(self, question):
        """Create true/false radio buttons"""
        group = QButtonGroup()
        true_radio = QRadioButton("True")
        false_radio = QRadioButton("False")
        
        true_radio.setStyleSheet("QRadioButton { font-size: 14px; padding: 8px; }")
        false_radio.setStyleSheet("QRadioButton { font-size: 14px; padding: 8px; }")
        
        group.addButton(true_radio, 0)
        group.addButton(false_radio, 1)
        
        self.answer_layout.addWidget(true_radio)
        self.answer_layout.addWidget(false_radio)
        
        # Check saved answer
        if self.current_question_index in self.user_answers:
            if self.user_answers[self.current_question_index] == 0:
                true_radio.setChecked(True)
            else:
                false_radio.setChecked(True)
        
        self.current_group = group
        group.buttonClicked.connect(lambda: self.save_answer(group.checkedId()))
    
    def create_identification_input(self, question):
        """Create text input for identification"""
        text_input = QTextEdit()
        text_input.setPlaceholderText("Type your answer here...")
        text_input.setMaximumHeight(120)
        text_input.setStyleSheet("QTextEdit { font-size: 13px; padding: 8px; }")
        self.answer_layout.addWidget(text_input)
        
        # Load saved answer
        if self.current_question_index in self.user_answers:
            text_input.setText(self.user_answers[self.current_question_index])
        
        text_input.textChanged.connect(lambda: self.save_answer(text_input.toPlainText()))
        self.current_input = text_input
    
    def create_essay_input(self, question):
        """Create text area for essay"""
        text_edit = QTextEdit()
        text_edit.setPlaceholderText("Type your essay answer here...")
        text_edit.setMinimumHeight(150)
        text_edit.setStyleSheet("QTextEdit { font-size: 13px; padding: 8px; }")
        self.answer_layout.addWidget(text_edit)
        
        # Load saved answer
        if self.current_question_index in self.user_answers:
            text_edit.setText(self.user_answers[self.current_question_index])
        
        text_edit.textChanged.connect(lambda: self.save_answer(text_edit.toPlainText()))
        self.current_input = text_edit
    
    def save_answer(self, answer):
        """Save user's answer"""
        self.user_answers[self.current_question_index] = answer
    
    def previous_question(self):
        """Go to previous question"""
        self.display_question(self.current_question_index - 1)
    
    def next_question(self):
        """Go to next question"""
        self.display_question(self.current_question_index + 1)
    
    def submit_quiz(self):
        """Submit quiz and show results"""
        # Create results window with reference answers if available
        results_window = ResultsWindow(self.questions, self.user_answers, self.reference_answers, self.fairytale_handler)
        results_window.show()
        self.result_windows_list.append(results_window)  # Keep reference to prevent garbage collection
        self.close()


class ResultsWindow(QMainWindow):
    """Display graded quiz results"""
    def __init__(self, questions, user_answers, reference_answers=None, fairytale_handler=None):
        super().__init__()
        self.setWindowTitle("Quiz Results")
        self.setGeometry(100, 100, 900, 700)
        
        self.questions = questions
        self.user_answers = user_answers
        self.reference_answers = reference_answers or []
        self.fairytale_handler = fairytale_handler
        
        # Calculate score
        self.correct_count = 0
        for i, question in enumerate(questions):
            if self.is_answer_correct(i, question):
                self.correct_count += 1
        
        score_percentage = (self.correct_count / len(questions) * 100) if questions else 0
        
        # Create main widget
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # Score display
        score_label = QLabel(f"Score: {self.correct_count}/{len(questions)} ({score_percentage:.1f}%)")
        score_label.setStyleSheet("font-size: 18px; font-weight: bold; padding: 20px; background-color: #f0f0f0;")
        main_layout.addWidget(score_label)
        
        # Scrollable results area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        results_widget = QWidget()
        results_layout = QVBoxLayout(results_widget)
        
        # Display each question and answer
        for i, question in enumerate(questions):
            self.add_result_item(results_layout, i, question)
        
        results_layout.addStretch()
        scroll.setWidget(results_widget)
        main_layout.addWidget(scroll)
        
        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        main_layout.addWidget(close_button)
        
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
    
    def is_answer_correct(self, index, question):
        """Check if user's answer is correct"""
        if index not in self.user_answers:
            return False
        
        user_answer = self.user_answers[index]
        correct_answer = question.get("answer", "")
        
        if question["type"] == "multiple_choice":
            # User answer is index, correct answer is letter
            if isinstance(user_answer, int):
                user_letter = chr(65 + user_answer)
                return user_letter == correct_answer
        elif question["type"] == "true_or_false":
            user_text = "True" if user_answer == 0 else "False"
            return user_text == correct_answer
        elif question["type"] == "identification":
            return user_answer.strip().lower() == correct_answer.lower()
        
        return False
    
    def add_result_item(self, layout, index, question):
        """Add a result item showing question and answer feedback"""
        group = QGroupBox(f"Question {index + 1}")
        group_layout = QVBoxLayout()
        
        # Question text
        q_label = QLabel(f"<b>{question['question']}</b>")
        q_label.setWordWrap(True)
        group_layout.addWidget(q_label)
        
        # User answer
        user_answer = self.user_answers.get(index, "Not answered")
        if question["type"] == "multiple_choice" and isinstance(user_answer, int):
            user_answer_text = f"{chr(65 + user_answer)}) {question['options'][user_answer]}"
        elif question["type"] == "true_or_false" and isinstance(user_answer, int):
            user_answer_text = "True" if user_answer == 0 else "False"
        else:
            user_answer_text = str(user_answer) if user_answer else "Not answered"
        
        user_label = QLabel(f"Your answer: {user_answer_text}")
        group_layout.addWidget(user_label)
        
        # Correct answer (only for non-essay questions)
        if question["type"] != "essay":
            correct_answer = question.get("answer", "")
            if question["type"] == "multiple_choice":
                idx = ord(correct_answer) - 65 if correct_answer else 0
                if idx < len(question.get("options", [])):
                    correct_answer = f"{correct_answer}) {question['options'][idx]}"
            
            correct_label = QLabel(f"Correct answer: {correct_answer}")
            correct_label.setStyleSheet("color: green; font-weight: bold;")
            group_layout.addWidget(correct_label)
        
        # Feedback
        is_correct = self.is_answer_correct(index, question)
        feedback_text = "✓ Correct" if is_correct else "✗ Incorrect"
        feedback_color = "green" if is_correct else "red"
        feedback_label = QLabel(feedback_text)
        feedback_label.setStyleSheet(f"color: {feedback_color}; font-size: 14px; font-weight: bold;")
        group_layout.addWidget(feedback_label)
        
        group.setLayout(group_layout)
        layout.addWidget(group)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    notebook = QWidget()
    question_setting = QuestionSetting()
    input_area = InputArea()
    generator = QuestionGenerator()

    question_input_layout = QVBoxLayout()
    question_input_layout.addWidget(input_area)
    question_input_layout.addWidget(question_setting)

    # Add Make button at bottom right
    button_layout = QHBoxLayout()
    button_layout.addStretch()
    make_button = QPushButton("Make")
    button_layout.addWidget(make_button)
    question_input_layout.addLayout(button_layout)

    notebook.setLayout(question_input_layout)

    result_windows = []
    
    # Initialize components
    print("Initializing question generator and FairytaleQA handler...")
    generator = QuestionGenerator()
    fairytale_handler = FairytaleQAHandler("fairytale_qa_data")
    
    def on_make_button_clicked():
        try:
            # Get text from input area
            text_input = input_area.input_message.toPlainText()
            
            if not text_input.strip():
                print("Please enter text to generate questions!")
                return
            
            # Get question types and quantities from settings (only if checkbox is checked)
            question_types = {}
            
            if question_setting.multiple_choice.isChecked():
                question_types["multiple_choice"] = question_setting.multiple_choice_spinbox.value()
            if question_setting.true_or_false.isChecked():
                question_types["true_or_false"] = question_setting.true_or_false_spinbox.value()
            if question_setting.identification.isChecked():
                question_types["identification"] = question_setting.identification_spinbox.value()
            if question_setting.essay.isChecked():
                question_types["essay"] = question_setting.essay_spinbox.value()
            
            if not question_types:
                print("Please select at least one question type!")
                return
            
            print(f"Generating questions with types: {question_types}")
            
            # Check if text matches a fairytale in dataset
            story_match = fairytale_handler.find_similar_story(text_input)
            if story_match and fairytale_handler.is_fairytale_dataset_available():
                print(f"✓ Detected fairytale from dataset: {story_match}")
                print("  Using FairytaleQA reference answers for enhanced grading")
            else:
                print("  Using standard grading (FairytaleQA data not available for this text)")
            
            # Generate questions using fine-tuned T5 model
            print("Generating questions using fine-tuned T5 model...")
            questions_text = generator.generate_questions(text_input, question_types, question_types)
            print(f"Generated text: {questions_text[:100]}...")
            
            # Parse questions into structured format
            questions = QuizParser.parse_questions(questions_text)
            print(f"✓ Parsed {len(questions)} questions")
            
            if not questions:
                print("Error parsing questions. Please try again.")
                return
            
            # Get reference answers if fairytale matched
            reference_answers = []
            if story_match and fairytale_handler.is_fairytale_dataset_available():
                reference_answers = fairytale_handler.get_reference_answers(story_match)
            
            # Show interactive quiz window
            quiz_window = QuizWindow(questions, result_windows, reference_answers, fairytale_handler)
            quiz_window.show()
            result_windows.append(quiz_window)
            print("✓ Quiz window opened successfully")
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
    
    make_button.clicked.connect(on_make_button_clicked)

    window = notebook
    window.show()
    app.exec()