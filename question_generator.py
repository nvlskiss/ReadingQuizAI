from transformers import T5Tokenizer, T5ForConditionalGeneration
import torch
import re

class QuestionGenerator:
    def __init__(self):
        # Use the fine-tuned T5 model from HuggingFace
        self.model_name = "mrm8488/t5-base-finetuned-question-generation-ap"
        
        print("Loading fine-tuned T5 model...")
        print("(This may take a moment on first run as models download automatically from HuggingFace)")
        
        try:
            self.tokenizer = T5Tokenizer.from_pretrained(self.model_name)
            self.model = T5ForConditionalGeneration.from_pretrained(self.model_name)
            
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.model.to(self.device)
            
            print(f"✓ Model loaded successfully on {self.device}")
        except Exception as e:
            print(f"✗ Error loading model: {e}")
            raise
    
    def generate_questions(self, text, question_types, quantities, language="English"):
        """Generate quiz questions using fine-tuned T5 model"""
        
        try:
            text = text.strip()
            if len(text) > 1000:
                text = text[:1000]
            
            # Extract sentences and key concepts
            sentences = self._split_sentences(text)
            questions_data = []
            
            for sentence in sentences:
                if len(questions_data) >= sum(quantities.values()):
                    break
                
                # Extract answer candidates (named entities, important nouns)
                answers = self._extract_key_phrases(sentence)
               
                for answer in answers:
                    if len(questions_data) >= sum(quantities.values()):
                        break
                    
                    # Generate question using proper T5 format
                    question = self._generate_question_for_answer(sentence, answer)
                    
                    if question:
                        questions_data.append({
                            'question': question,
                            'answer': answer,
                            'sentence': sentence
                        })
            
            if not questions_data:
                return "Error: Could not generate questions from the text."
            
            # Format according to requested types
            return self._format_by_type(questions_data, quantities)
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            return f"Error: {str(e)}"
    
    def _split_sentences(self, text):
        """Split text into sentences"""
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if len(s.strip()) > 15]
    
    def _extract_key_phrases(self, sentence):
        """Extract key named entities and important nouns"""
        # First, get capitalized words (proper nouns)
        words = sentence.split()
        proper_nouns = []
        
        for word in words:
            cleaned = word.strip(',;:"!?.').lower()
            if word and word[0].isupper() and len(word) > 2 and cleaned not in ['the', 'a', 'an']:
                proper_nouns.append(word.strip(',;:"!?.'))
        
        if proper_nouns:
            return proper_nouns[:2]
        
        # If no proper nouns, extract longer nouns
        stop_words = {'is', 'are', 'was', 'were', 'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'it', 'that', 'this', 'which', 'who', 'what', 'when', 'where', 'why', 'how'}
        
        candidates = []
        for word in words:
            cleaned = word.strip(',;:"!?.').lower()
            if len(cleaned) > 4 and cleaned not in stop_words:
                candidates.append(word.strip(',;:"!?.'))
        
        return candidates[:2] if candidates else []
    
    def _generate_question_for_answer(self, sentence, answer):
        """Generate a question for the given answer using T5"""
        # Use T5's expected format
        prompt = f"answer_token: {answer} context: {sentence}"
        
        inputs = self.tokenizer.encode(prompt, return_tensors="pt", max_length=256, truncation=True)
        inputs = inputs.to(self.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                inputs,
                max_length=100,
                num_beams=4,
                temperature=0.7,
                do_sample=True,
                top_p=0.9
            )
        
        question = self.tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
        
        # Clean up T5 output
        question = re.sub(r'^question:\s*', '', question, flags=re.IGNORECASE)
        
        return question if len(question) > 8 else None
    
    def _format_by_type(self, questions_data, quantities):
        """Format questions according to requested types and return as formatted string"""
        
        formatted = ""
        q_num = 1
        q_idx = 0
        
        # Multiple Choice
        mc_count = quantities.get("multiple_choice", 0)
        for i in range(mc_count):
            if q_idx < len(questions_data):
                q = questions_data[q_idx]
                options = [q['answer']] + self._get_distractors(q['sentence'], q['answer'], 3)
                
                formatted += f"{q_num}. {q['question']}\n"
                formatted += f"A) {options[0]}\n"
                formatted += f"B) {options[1] if len(options) > 1 else 'Option 2'}\n"
                formatted += f"C) {options[2] if len(options) > 2 else 'Option 3'}\n"
                formatted += f"D) {options[3] if len(options) > 3 else 'Option 4'}\n"
                formatted += "Answer: A\n\n"
                q_num += 1
                q_idx += 1
        
        # Identification
        id_count = quantities.get("identification", 0)
        for i in range(id_count):
            if q_idx < len(questions_data):
                q = questions_data[q_idx]
                formatted += f"{q_num}. {q['question']}\n"
                formatted += f"Answer: {q['answer']}\n\n"
                q_num += 1
                q_idx += 1
        
        # Essay
        essay_count = quantities.get("essay", 0)
        for i in range(essay_count):
            if q_idx < len(questions_data):
                q = questions_data[q_idx]
                formatted += f"{q_num}. {q['question']}\n\n"
                q_num += 1
                q_idx += 1
        
        return formatted
    
    def _get_distractors(self, sentence, correct_answer, count=3):
        """Get plausible distractor options from the sentence"""
        words = sentence.split()
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'it', 'that', 'this', 'which', 'who'}
        
        candidates = []
        for word in words:
            cleaned = word.strip(',;:"!?.').lower()
            if (cleaned not in stop_words and 
                cleaned != correct_answer.lower() and 
                len(word.strip(',;:"!?.')) > 2):
                candidates.append(word.strip(',;:"!?.'))
        
        # Remove duplicates while preserving order
        seen = set()
        unique = []
        for c in candidates:
            if c.lower() not in seen:
                seen.add(c.lower())
                unique.append(c)
        
        return unique[:count] if unique else ['Option 2', 'Option 3', 'Option 4']
