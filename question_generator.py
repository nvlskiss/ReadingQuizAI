from transformers import T5Tokenizer, T5ForConditionalGeneration
import torch
import re
import random
import difflib
import os


class QuestionGenerator:
    def __init__(self):
        self.base_model_name = "mrm8488/t5-base-finetuned-question-generation-ap"
        self.local_model_dir = os.getenv("READINGQUIZ_MODEL_DIR", "models/qg_verify_full")
        self.model_name = self._resolve_model_source()

        print("Loading fine-tuned T5 model...")
        print(f"Model source: {self.model_name}")
        print("(This may take a moment on first run as models download automatically from HuggingFace)")

        try:
            self.tokenizer = T5Tokenizer.from_pretrained(self.model_name)
            self.model = T5ForConditionalGeneration.from_pretrained(self.model_name)

            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.model.to(self.device)
            self.random = random.Random()
            self.weak_answer_words = {
                "while", "when", "where", "because", "although", "though", "since", "until", "after",
                "before", "during", "through", "and", "or", "but", "then", "than", "just", "very",
                "there", "their", "every", "some", "many", "much", "one", "two", "three"
            }
            self.semantic_pools = {
                "time_of_day": ["morning", "afternoon", "evening", "night", "dawn", "noon", "midnight"],
                "duration": ["minutes", "an hour", "hours", "a day", "days", "a week", "weeks", "long ago"],
                "frequency": ["always", "often", "sometimes", "rarely", "never", "daily", "weekly"],
                "number": ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"],
                "direction": ["left", "right", "north", "south", "east", "west", "up", "down"],
                "generic_noun": [],
            }

            print(f"✓ Model loaded successfully on {self.device}")
        except Exception as error:
            print(f"✗ Error loading model: {error}")
            raise

    def _resolve_model_source(self):
        if not os.path.isdir(self.local_model_dir):
            return self.base_model_name

        config_path = os.path.join(self.local_model_dir, "config.json")
        if os.path.isfile(config_path):
            return self.local_model_dir

        checkpoint_dirs = []
        for child in os.listdir(self.local_model_dir):
            if child.startswith("checkpoint-"):
                full_path = os.path.join(self.local_model_dir, child)
                if os.path.isdir(full_path):
                    checkpoint_dirs.append(full_path)

        if checkpoint_dirs:
            checkpoint_dirs.sort(key=lambda path: int(path.rsplit("checkpoint-", 1)[-1]))
            return checkpoint_dirs[-1]

        return self.base_model_name

    def generate_questions(self, text, question_types, quantities, language="English"):
        try:
            text = self._normalize_text(text)
            if len(text) > 1000:
                text = text[:1000]

            sentences = self._split_sentences(text)
            questions_data = []
            seen_pairs = set()
            target_count = sum(quantities.values())

            for sentence in sentences:
                if len(questions_data) >= target_count:
                    break

                answers = self._extract_key_phrases(sentence)
                for answer in answers:
                    if len(questions_data) >= target_count:
                        break

                    pair_key = (sentence.lower(), answer.lower())
                    if pair_key in seen_pairs:
                        continue

                    question = self._generate_question_for_answer(sentence, answer)
                    if question:
                        seen_pairs.add(pair_key)
                        questions_data.append(
                            {
                                "question": question,
                                "answer": answer,
                                "sentence": sentence,
                            }
                        )
                        break

            if not questions_data:
                return "Error: Could not generate questions from the text."

            return self._format_by_type(questions_data, quantities)

        except Exception as error:
            print(f"Error: {error}")
            import traceback
            traceback.print_exc()
            return f"Error: {str(error)}"

    def _split_sentences(self, text):
        raw_sentences = re.split(r"[.!?]+", text)
        cleaned_sentences = []
        for raw_sentence in raw_sentences:
            cleaned = self._normalize_text(raw_sentence)
            if len(cleaned) > 20:
                cleaned_sentences.append(cleaned)
        return cleaned_sentences

    def _extract_key_phrases(self, sentence):
        words = re.findall(r"[A-Za-z][A-Za-z'\-]*", sentence)
        if not words:
            return []

        time_phrases = self._extract_time_phrases(sentence)

        stop_words = {
            "is", "are", "was", "were", "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "be", "been", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "must", "can", "it", "that", "this", "which", "who",
            "what", "when", "where", "why", "how", "there", "their", "then", "than", "very", "just", "while",
            "after", "before", "during", "since", "until", "every"
        }

        proper_nouns = []
        for index, word in enumerate(words):
            cleaned_word = self._clean_token(word)
            if not cleaned_word:
                continue
            is_probable_proper_noun = (
                word[0].isupper()
                and len(cleaned_word) > 2
                and cleaned_word.lower() not in stop_words
            )
            if is_probable_proper_noun and index != 0 and self._is_valid_answer_candidate(cleaned_word):
                proper_nouns.append(cleaned_word)

        if proper_nouns:
            return (time_phrases + proper_nouns)[:3]

        candidates = []
        for word in words:
            cleaned_word = self._clean_token(word)
            if len(cleaned_word) > 3 and cleaned_word.lower() not in stop_words and self._is_valid_answer_candidate(cleaned_word):
                candidates.append(cleaned_word)

        unique_candidates = []
        seen = set()
        for candidate in candidates:
            lowered = candidate.lower()
            if lowered not in seen:
                seen.add(lowered)
                unique_candidates.append(candidate)

        return (time_phrases + unique_candidates)[:3]

    def _generate_question_for_answer(self, sentence, answer):
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
                top_p=0.9,
            )

        question = self.tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
        question = re.sub(r"^question:\s*", "", question, flags=re.IGNORECASE)
        question = self._normalize_text(question)

        if not question.endswith("?"):
            question = f"{question}?"

        if len(question) <= 8:
            return None

        if answer.lower() in question.lower():
            return None

        return question

    def _format_by_type(self, questions_data, quantities):
        formatted = ""
        q_num = 1
        tf_created = 0
        used_contexts = set()
        used_question_texts = set()
        used_tf_statements = set()

        question_pool = list(questions_data)
        self.random.shuffle(question_pool)

        requested_types = []
        for question_type in ("multiple_choice", "true_or_false", "identification", "essay"):
            requested_types.extend([question_type] * quantities.get(question_type, 0))
        self.random.shuffle(requested_types)

        for question_type in requested_types:
            selected_index = None
            selected_item = None
            selected_statement = None
            selected_tf_answer = None
            selected_statement_key = None

            for index, question_data in enumerate(question_pool):
                context_key = self._normalize_text(question_data["sentence"]).lower()
                if context_key in used_contexts:
                    continue

                normalized_question = question_data["question"].strip().lower()
                if normalized_question in used_question_texts:
                    continue

                if question_type == "true_or_false":
                    statement, tf_answer = self._build_true_false_item(question_data, tf_created)
                    statement_key = self._normalize_text(statement).lower()
                    if statement_key in used_tf_statements:
                        continue

                    selected_index = index
                    selected_item = question_data
                    selected_statement = statement
                    selected_tf_answer = tf_answer
                    selected_statement_key = statement_key
                    break

                selected_index = index
                selected_item = question_data
                break

            if selected_item is None:
                continue

            question_pool.pop(selected_index)

            context_key = self._normalize_text(selected_item["sentence"]).lower()
            normalized_question = selected_item["question"].strip().lower()
            used_contexts.add(context_key)
            used_question_texts.add(normalized_question)

            if question_type == "multiple_choice":
                options, answer_label = self._build_multiple_choice_options(selected_item)
                formatted += f"{q_num}. {selected_item['question']}\n"
                formatted += f"A) {options[0]}\n"
                formatted += f"B) {options[1]}\n"
                formatted += f"C) {options[2]}\n"
                formatted += f"D) {options[3]}\n"
                formatted += f"Answer: {answer_label}\n"
                formatted += f"Context: {self._format_context(selected_item['sentence'])}\n\n"
                q_num += 1
                continue

            if question_type == "true_or_false":
                used_tf_statements.add(selected_statement_key)
                formatted += f"{q_num}. True or False: {selected_statement}\n"
                formatted += f"Answer: {selected_tf_answer}\n"
                formatted += f"Context: {self._format_context(selected_item['sentence'])}\n\n"
                q_num += 1
                tf_created += 1
                continue

            if question_type == "identification":
                formatted += f"{q_num}. {selected_item['question']}\n"
                formatted += f"Answer: {selected_item['answer']}\n"
                formatted += f"Context: {self._format_context(selected_item['sentence'])}\n\n"
                q_num += 1
                continue

            if question_type == "essay":
                formatted += f"{q_num}. {selected_item['question']}\n"
                formatted += f"Context: {self._format_context(selected_item['sentence'])}\n\n"
                q_num += 1

        return formatted

    def _build_true_false_item(self, question_data, index):
        statement = question_data["sentence"].strip()
        make_false = index % 2 == 1

        if make_false:
            false_statement = self._create_false_statement(question_data)
            if false_statement:
                statement = false_statement
                answer = "False"
            else:
                answer = "True"
        else:
            answer = "True"

        if statement and not statement.endswith("."):
            statement += "."

        return statement, answer

    def _create_false_statement(self, question_data):
        sentence = question_data["sentence"].strip()
        answer = question_data["answer"].strip()

        candidates = [
            self._replace_time_expression(sentence),
            self._replace_number_expression(sentence),
            self._replace_answer_token(sentence, answer),
            self._toggle_negation(sentence),
        ]

        for candidate in candidates:
            if self._is_valid_false_statement(sentence, candidate):
                return candidate

        return None

    def _negate_sentence(self, sentence):
        patterns = [
            (r"\b(is|are|was|were|has|have|had|can|could|will|would|should|may|might|must)\b", r"\1 not"),
            (r"\b(do|does|did)\b", r"\1 not"),
        ]

        for pattern, replacement in patterns:
            negated, count = re.subn(pattern, replacement, sentence, count=1, flags=re.IGNORECASE)
            if count > 0:
                return negated

        return sentence

    def _replace_time_expression(self, sentence):
        time_pattern = r"\b(morning|afternoon|evening|night|noon|midnight|dawn)\b"
        match = re.search(time_pattern, sentence, flags=re.IGNORECASE)
        if not match:
            return None

        original = match.group(1)
        replacement_candidates = [
            item for item in self.semantic_pools["time_of_day"] if item.lower() != original.lower()
        ]
        if not replacement_candidates:
            return None

        replacement = self.random.choice(replacement_candidates)
        return re.sub(time_pattern, replacement, sentence, count=1, flags=re.IGNORECASE)

    def _replace_number_expression(self, sentence):
        number_pattern = r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\b"
        match = re.search(number_pattern, sentence, flags=re.IGNORECASE)
        if not match:
            return None

        original = match.group(1)
        replacement_candidates = [
            item for item in self.semantic_pools["number"] if item.lower() != original.lower()
        ]
        if not replacement_candidates:
            return None

        replacement = self.random.choice(replacement_candidates)
        return re.sub(number_pattern, replacement, sentence, count=1, flags=re.IGNORECASE)

    def _replace_answer_token(self, sentence, answer):
        if not answer:
            return None

        cleaned_answer = self._clean_token(answer)
        if not cleaned_answer or not self._is_valid_answer_candidate(cleaned_answer):
            return None

        answer_type = self._infer_answer_type(cleaned_answer)
        semantic_distractors = self._get_semantic_distractors(cleaned_answer, 5)
        context_distractors = self._get_distractors(sentence, cleaned_answer, 8)
        replacement_candidates = semantic_distractors + context_distractors

        for candidate in replacement_candidates:
            replacement = self._clean_token(candidate)
            if not replacement:
                continue
            if replacement.lower() == cleaned_answer.lower():
                continue
            if answer_type == "generic_noun" and replacement.lower() in self.weak_answer_words:
                continue

            pattern = re.compile(rf"\b{re.escape(cleaned_answer)}\b", flags=re.IGNORECASE)
            swapped = pattern.sub(replacement, sentence, count=1)
            if swapped != sentence:
                return swapped

        return None

    def _toggle_negation(self, sentence):
        contraction_patterns = [
            (r"\bwasn't\b", "was"),
            (r"\bweren't\b", "were"),
            (r"\bisn't\b", "is"),
            (r"\baren't\b", "are"),
            (r"\bhasn't\b", "has"),
            (r"\bhaven't\b", "have"),
            (r"\bhadn't\b", "had"),
            (r"\bcan't\b", "can"),
            (r"\bcouldn't\b", "could"),
            (r"\bwon't\b", "will"),
            (r"\bwouldn't\b", "would"),
            (r"\bshouldn't\b", "should"),
            (r"\bdidn't\b", "did"),
            (r"\bdoesn't\b", "does"),
            (r"\bdon't\b", "do"),
        ]

        for pattern, replacement in contraction_patterns:
            toggled, count = re.subn(pattern, replacement, sentence, count=1, flags=re.IGNORECASE)
            if count > 0:
                return toggled

        remove_not_patterns = [
            (r"\b(is|are|was|were|has|have|had|can|could|will|would|should|may|might|must)\s+not\b", r"\1"),
            (r"\b(do|does|did)\s+not\b", r"\1"),
        ]

        for pattern, replacement in remove_not_patterns:
            toggled, count = re.subn(pattern, replacement, sentence, count=1, flags=re.IGNORECASE)
            if count > 0:
                return toggled

        return self._negate_sentence(sentence)

    def _is_valid_false_statement(self, original, candidate):
        if not candidate:
            return False

        original_clean = self._normalize_text(original)
        candidate_clean = self._normalize_text(candidate)
        if not candidate_clean or candidate_clean.lower() == original_clean.lower():
            return False

        if re.search(r"\b(\w+)\s+\1\b", candidate_clean, flags=re.IGNORECASE):
            return False

        if len(candidate_clean) < 12:
            return False

        if self._count_meaningful_token_changes(original_clean, candidate_clean) < 2:
            return False

        return True

    def _count_meaningful_token_changes(self, original, candidate):
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been", "and", "or", "but", "in", "on", "at",
            "to", "for", "of", "with", "by", "from", "it", "that", "this", "which", "who", "there", "their",
            "as", "into", "onto", "up", "down", "out", "about",
        }

        original_tokens = re.findall(r"[A-Za-z0-9']+", original.lower())
        candidate_tokens = re.findall(r"[A-Za-z0-9']+", candidate.lower())
        matcher = difflib.SequenceMatcher(a=original_tokens, b=candidate_tokens)

        changed_tokens = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                continue
            changed_tokens.extend(original_tokens[i1:i2])
            changed_tokens.extend(candidate_tokens[j1:j2])

        meaningful_changes = [token for token in changed_tokens if token not in stop_words and len(token) > 2]
        return len(set(meaningful_changes))

    def _get_distractors(self, sentence, correct_answer, count=3):
        words = re.findall(r"[A-Za-z][A-Za-z'\-]*", sentence)
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been", "and", "or", "but", "in", "on", "at",
            "to", "for", "of", "with", "by", "from", "it", "that", "this", "which", "who", "there", "their",
        }

        candidates = []
        for word in words:
            cleaned = self._clean_token(word).lower()
            if cleaned not in stop_words and cleaned != correct_answer.lower() and len(cleaned) > 2:
                candidates.append(self._clean_token(word))

        seen = set()
        unique = []
        for candidate in candidates:
            if candidate.lower() not in seen:
                seen.add(candidate.lower())
                unique.append(candidate)

        return unique[:count]

    def _build_multiple_choice_options(self, question_data):
        correct_answer = self._clean_token(question_data["answer"])
        semantic_distractors = self._get_semantic_distractors(correct_answer, 4)
        context_distractors = self._get_distractors(question_data["sentence"], correct_answer, 8)
        distractors = semantic_distractors + context_distractors

        cleaned_distractors = []
        for distractor in distractors:
            cleaned = self._clean_token(distractor)
            if cleaned and cleaned.lower() != correct_answer.lower():
                cleaned_distractors.append(cleaned)

        unique_distractors = []
        seen = set()
        for distractor in cleaned_distractors:
            lowered = distractor.lower()
            if lowered not in seen:
                seen.add(lowered)
                unique_distractors.append(distractor)

        answer_type = self._infer_answer_type(correct_answer)
        fallback_options = self.semantic_pools.get(answer_type, [])
        for fallback_option in fallback_options:
            if len(unique_distractors) >= 3:
                break
            if fallback_option.lower() != correct_answer.lower() and fallback_option.lower() not in seen:
                seen.add(fallback_option.lower())
                unique_distractors.append(fallback_option)

        options = [correct_answer] + unique_distractors[:3]
        while len(options) < 4:
            options.append(f"Option {len(options) + 1}")

        self.random.shuffle(options)
        answer_index = options.index(correct_answer)
        answer_label = ["A", "B", "C", "D"][answer_index]

        return options, answer_label

    def _extract_time_phrases(self, sentence):
        patterns = [
            r"\b(morning|afternoon|evening|night|noon|midnight|dawn)\b",
            r"\b(an hour|a day|a week|\d+\s+(minute|minutes|hour|hours|day|days|week|weeks))\b",
            r"\b(long ago|later|earlier)\b",
        ]

        extracted = []
        seen = set()
        lowered_sentence = sentence.lower()
        for pattern in patterns:
            for match in re.finditer(pattern, lowered_sentence, flags=re.IGNORECASE):
                phrase = match.group(1) if match.lastindex else match.group(0)
                cleaned = self._clean_token(phrase)
                if cleaned and cleaned.lower() not in seen and self._is_valid_answer_candidate(cleaned):
                    seen.add(cleaned.lower())
                    extracted.append(cleaned)
        return extracted

    def _is_valid_answer_candidate(self, candidate):
        lowered = candidate.lower()
        if lowered in self.weak_answer_words:
            return False
        if len(lowered) <= 2:
            return False
        if re.fullmatch(r"\d+", lowered):
            return False
        return True

    def _infer_answer_type(self, answer):
        lowered = answer.lower().strip()

        if lowered in self.semantic_pools["time_of_day"]:
            return "time_of_day"

        if any(token in lowered for token in ["minute", "hour", "day", "week", "ago"]):
            return "duration"

        if lowered in self.semantic_pools["frequency"]:
            return "frequency"

        if lowered in self.semantic_pools["number"] or re.fullmatch(r"\d+", lowered):
            return "number"

        if lowered in self.semantic_pools["direction"]:
            return "direction"

        return "generic_noun"

    def _get_semantic_distractors(self, correct_answer, count):
        answer_type = self._infer_answer_type(correct_answer)
        pool = self.semantic_pools.get(answer_type, [])

        distractors = [item for item in pool if item.lower() != correct_answer.lower()]
        self.random.shuffle(distractors)
        return distractors[:count]

    def _clean_token(self, token):
        cleaned = self._normalize_text(token)
        cleaned = re.sub(r"^[^A-Za-z0-9]+|[^A-Za-z0-9]+$", "", cleaned)
        return cleaned

    def _format_context(self, sentence):
        context = self._normalize_text(sentence)
        if context and not context.endswith("."):
            context += "."
        return context

    def _normalize_text(self, text):
        normalized = str(text)
        normalized = normalized.replace("\u2019", "'")
        normalized = normalized.replace("\u2018", "'")
        normalized = normalized.replace("\u201c", '"')
        normalized = normalized.replace("\u201d", '"')
        normalized = normalized.replace("\u2014", "-")
        normalized = normalized.replace("\u2013", "-")
        normalized = normalized.replace("**", "")
        normalized = re.sub(r"\s+", " ", normalized)
        normalized = re.sub(r"\s*—\s*", " - ", normalized)
        normalized = normalized.replace("_", "")
        return normalized.strip()
