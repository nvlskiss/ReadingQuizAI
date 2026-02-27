import re

class QuizParser:
    """Parse AI-generated quiz content into structured question data"""
    
    @staticmethod
    def parse_questions(content, verbose=False):
        """
        Parse quiz content and extract structured questions.
        Designed to work with T5 output formatted with explicit numbered questions.
        
        Returns:
            list of dict: [{"type": "...", "question": "...", "options": [...], "answer": "..."}]
        """
        questions = []
        
        # Split by numbered questions (1., 2., 3., etc.)
        pattern = r'\n\s*(\d+)\.\s+(.+?)(?=\n\s*\d+\.|$)'
        matches = re.finditer(pattern, content, re.DOTALL)
        
        for match in matches:
            q_block = match.group(2).strip()
            parsed_q = QuizParser._parse_single_question(q_block)
            if parsed_q:
                questions.append(parsed_q)
        
        return questions
    
    @staticmethod
    def _parse_single_question(block):
        """Parse a single question block"""
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        
        if not lines:
            return None
        
        question_text = lines[0]
        
        # Detect question type and parse accordingly
        if QuizParser._is_multiple_choice(block):
            return QuizParser._parse_multiple_choice(question_text, block)
        elif QuizParser._is_true_false(block):
            return QuizParser._parse_true_false(question_text, block)
        elif QuizParser._is_identification(question_text, block):
            return QuizParser._parse_identification(question_text, block)
        elif 'essay' in block.lower():
            return QuizParser._parse_essay(question_text, block)
        else:
            # Default: try MC, then T/F, then ID
            if QuizParser._is_multiple_choice(block):
                return QuizParser._parse_multiple_choice(question_text, block)
            else:
                return QuizParser._parse_identification(question_text, block)
    
    @staticmethod
    def _is_multiple_choice(block):
        """Check if block contains multiple choice options (A), B), C), D))"""
        return bool(re.search(r'^[A-D]\)', block, re.MULTILINE))
    
    @staticmethod
    def _is_true_false(block):
        """Check if block is a True/False question"""
        return bool(re.search(r'Answer:\s*(True|False)', block, re.IGNORECASE))
    
    @staticmethod
    def _is_identification(question_text, block):
        """Check if it's an identification question"""
        # If there are options, it's not identification
        if re.search(r'^[A-D]\)', block, re.MULTILINE):
            return False
        # If it has True/False answer, it's not identification
        if re.search(r'Answer:\s*(True|False)', block, re.IGNORECASE):
            return False
        return True
    
    @staticmethod
    def _parse_multiple_choice(question_text, block):
        """Parse multiple choice question"""
        lines = block.split('\n')
        
        options = []
        correct_answer = None
        
        for line in lines:
            line = line.strip()
            # Extract options A), B), C), D)
            option_match = re.match(r'([A-D])\)\s+(.+)', line)
            if option_match:
                letter = option_match.group(1)
                text = option_match.group(2)
                options.append(text)
            
            # Extract answer
            answer_match = re.search(r'Answer:\s*([A-D])', line, re.IGNORECASE)
            if answer_match:
                correct_answer = answer_match.group(1)
        
        if len(options) >= 2 and correct_answer:
            return {
                "type": "multiple_choice",
                "question": question_text,
                "options": options,
                "answer": correct_answer
            }
        
        return None
    
    @staticmethod
    def _parse_true_false(question_text, block):
        """Parse true/false question"""
        answer_match = re.search(r'Answer:\s*(True|False)', block, re.IGNORECASE)
        answer = answer_match.group(1) if answer_match else "True"
        
        return {
            "type": "true_or_false",
            "question": question_text,
            "answer": answer
        }
    
    @staticmethod
    def _parse_identification(question_text, block):
        """Parse identification question"""
        answer_match = re.search(r'Answer:\s*(.+?)(?:\n|$)', block)
        answer = answer_match.group(1).strip() if answer_match else ""
        
        return {
            "type": "identification",
            "question": question_text,
            "answer": answer
        }
    
    @staticmethod
    def _parse_essay(question_text, block):
        """Parse essay question"""
        answer_match = re.search(r'Answer:\s*(.+?)(?:\n|$)', block)
        answer = answer_match.group(1).strip() if answer_match else ""
        
        return {
            "type": "essay",
            "question": question_text,
            "answer": answer
        }
