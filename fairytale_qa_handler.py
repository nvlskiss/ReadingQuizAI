import json
import os
from pathlib import Path
from difflib import SequenceMatcher

class FairytaleQAHandler:
    """Manages FairytaleQA dataset for answer validation and grading"""
    
    def __init__(self, dataset_path="fairytale_qa_data"):
        self.dataset_path = Path(dataset_path)
        self.stories = {}
        self.answer_bank = {}
        self._load_dataset()
    
    def _load_dataset(self):
        """Load FairytaleQA dataset from JSON files"""
        try:
            if not self.dataset_path.exists():
                print(f"Warning: FairytaleQA dataset not found at {self.dataset_path}")
                return
            
            # Load all JSON files from the dataset
            json_files = list(self.dataset_path.glob("**/*.json"))
            print(f"Found {len(json_files)} JSON files in FairytaleQA dataset")
            
            for json_file in json_files:
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                        # Handle different dataset formats
                        if isinstance(data, dict):
                            for story_id, story_data in data.items():
                                self.stories[story_id] = story_data
                                
                                # Build answer bank for grading reference
                                if "questions" in story_data:
                                    for q_id, question_data in story_data["questions"].items():
                                        self.answer_bank[q_id] = {
                                            "answer": question_data.get("answer", ""),
                                            "type": question_data.get("type", "factual"),
                                            "story": story_id
                                        }
                        elif isinstance(data, list):
                            for item in data:
                                if "story_id" in item:
                                    self.stories[item["story_id"]] = item
                except Exception as e:
                    print(f"Warning: Error loading {json_file}: {e}")
            
            print(f"✓ Loaded {len(self.stories)} stories from FairytaleQA dataset")
            print(f"✓ Indexed {len(self.answer_bank)} QA pairs for grading reference")
            
        except Exception as e:
            print(f"Warning: Could not load FairytaleQA dataset: {e}")
    
    def find_similar_story(self, user_text):
        """Check if user input matches any fairytale in dataset"""
        if not self.stories:
            return None
        
        best_match = None
        best_ratio = 0
        
        try:
            for story_id, story_data in self.stories.items():
                # Try to get story text from different possible keys
                story_text = (story_data.get("story", "") or 
                            story_data.get("text", "") or 
                            str(story_data))
                
                # Compare first 500 chars for efficiency
                user_sample = user_text.lower()[:500]
                story_sample = story_text.lower()[:500]
                
                ratio = SequenceMatcher(None, user_sample, story_sample).ratio()
                
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_match = story_id
        except Exception as e:
            print(f"Error finding similar story: {e}")
        
        # Return match if similarity is above 40%
        return best_match if best_ratio > 0.4 else None
    
    def get_reference_answers(self, story_id):
        """Get reference answers from dataset for better grading"""
        if not story_id or story_id not in self.stories:
            return []
        
        reference_answers = []
        story_data = self.stories[story_id]
        
        try:
            # Handle different dataset formats
            if "questions" in story_data and isinstance(story_data["questions"], dict):
                for q_id, question_data in story_data["questions"].items():
                    reference_answers.append({
                        "id": q_id,
                        "question": question_data.get("question", ""),
                        "answer": question_data.get("answer", ""),
                        "type": question_data.get("type", "factual"),
                        "keywords": question_data.get("answer", "").split()[:5],
                        "source": "fairytale_qa"
                    })
            elif "questions" in story_data and isinstance(story_data["questions"], list):
                for i, question_data in enumerate(story_data["questions"]):
                    reference_answers.append({
                        "id": f"{story_id}_{i}",
                        "question": question_data.get("question", ""),
                        "answer": question_data.get("answer", ""),
                        "type": question_data.get("type", "factual"),
                        "keywords": question_data.get("answer", "").split()[:5],
                        "source": "fairytale_qa"
                    })
        except Exception as e:
            print(f"Error extracting reference answers: {e}")
        
        return reference_answers
    
    def grade_answer_with_reference(self, user_answer, reference_answer):
        """Smart grading using FairytaleQA reference answers
        
        Returns:
            float: Score from 0.0 to 1.0
        """
        if not user_answer or not reference_answer:
            return 0.0
        
        user_ans_lower = user_answer.strip().lower()
        ref_ans_lower = reference_answer.strip().lower()
        
        # Exact match (100% correct)
        if user_ans_lower == ref_ans_lower:
            return 1.0
        
        # Keyword matching (partial credit)
        keywords = [kw for kw in ref_ans_lower.split() if len(kw) > 3]
        if keywords:
            matched = sum(1 for kw in keywords if kw in user_ans_lower)
            keyword_score = matched / len(keywords) if len(keywords) > 0 else 0
            
            if keyword_score > 0.5:
                return keyword_score
        
        # Similarity ratio as fallback
        ratio = SequenceMatcher(None, user_ans_lower, ref_ans_lower).ratio()
        return ratio if ratio > 0.5 else 0.0
    
    def is_fairytale_dataset_available(self):
        """Check if FairytaleQA dataset is loaded"""
        return len(self.stories) > 0
