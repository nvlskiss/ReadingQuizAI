from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, T5ForConditionalGeneration, T5Tokenizer
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
        self.translation_model_names = {
            "tl_en": "Helsinki-NLP/opus-mt-tl-en",
            "en_tl": "Helsinki-NLP/opus-mt-en-tl",
        }
        self.translation_resources = {}
        self.translation_cache = {}
        self.filipino_spelling_corrections = {
            "naggibigay": "nagbibigay",
            "nagbibgy": "nagbibigay",
            "iervesptop": "river stop",
        }

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
            self.low_value_answer_words = {
                "everyone", "everything", "someone", "somebody", "anyone", "anybody", "nobody", "nothing",
                "something", "anything", "least", "most", "said", "says", "say", "thing", "things",
                "that", "this", "these", "those", "it", "its", "it's", "thats", "that's", "what",
                "small", "large", "big", "dark", "light", "warm", "cold", "sat", "rest",
                "who", "whom", "whose", "which", "where", "when", "why", "how", "pause", "paused"
            }
            self.common_verb_tokens = {
                "is", "are", "was", "were", "be", "been", "being", "am",
                "do", "does", "did", "has", "have", "had",
                "go", "goes", "went", "gone", "come", "comes", "came",
                "sit", "sits", "sat", "stand", "stands", "stood",
                "look", "looks", "looked", "seem", "seems", "seemed",
                "turn", "turns", "turned", "become", "becomes", "became",
                "grow", "grows", "grew", "fall", "falls", "fell", "pause", "pauses", "paused",
            }
            self.filipino_function_words = {
                "ang", "ng", "sa", "mga", "si", "ni", "kay", "kina", "nang", "na", "at",
                "pero", "dahil", "kung", "kapag", "habang", "para", "mula", "ito", "iyan", "iyon",
                "isang", "isang", "may", "mga", "rin", "din", "pa", "lamang", "lang"
            }
            self.semantic_pools = {
                "time_of_day": ["morning", "afternoon", "evening", "night", "dawn", "noon", "midnight"],
                "duration": ["minutes", "an hour", "hours", "a day", "days", "a week", "weeks", "long ago"],
                "frequency": ["always", "often", "sometimes", "rarely", "never", "daily", "weekly"],
                "number": ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"],
                "direction": ["left", "right", "north", "south", "east", "west", "up", "down"],
                "generic_noun": [],
            }
            self.entity_fallback_pools = {
                "person": ["the teacher", "the student", "the traveler", "the narrator", "the child", "the elder"],
                "place": ["the house", "the village", "the town", "the road", "the market", "the garden"],
                "creature": ["the bird", "the dog", "the cat", "the horse", "the wolf", "the lion"],
                "title": ["the story", "the tale", "the legend", "the chapter", "the article", "the passage"],
                "action": ["went silent", "turned pale", "fell asleep", "grew weak", "looked away", "stood still"],
                "object": ["the lamp", "the key", "the box", "the letter", "the ring", "the book"],
                "unknown": ["another detail", "another event", "another reason", "another object", "another place", "another person"],
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

            language_normalized = self._normalize_text(language).lower()
            is_filipino_mode = language_normalized == "filipino"

            if is_filipino_mode:
                original_sentences = self._split_sentences(text)
                translated_sentences = []
                for sentence in original_sentences:
                    translated_sentence = self._translate_text(sentence, "tl_en")
                    translated_sentence = self._normalize_text(translated_sentence)
                    if len(translated_sentence) > 20:
                        translated_sentences.append(translated_sentence)
                sentences = translated_sentences or self._split_sentences(text)
            else:
                sentences = self._split_sentences(text)
            questions_data = []
            seen_pairs = set()
            target_count = sum(quantities.values())

            for sentence in sentences:
                if len(questions_data) >= target_count:
                    break

                if not self._is_sentence_informative(sentence):
                    continue

                answers = self._extract_key_phrases(sentence)
                scored_entries = []

                for answer in answers:
                    if len(questions_data) >= target_count:
                        break

                    pair_key = (sentence.lower(), answer.lower())
                    if pair_key in seen_pairs:
                        continue

                    question = self._generate_question_for_answer(sentence, answer)
                    if question:
                        quality_score = self._score_question_candidate(question, answer, sentence)
                        scored_entries.append(
                            {
                                "pair_key": pair_key,
                                "question": question,
                                "answer": answer,
                                "sentence": sentence,
                                "score": quality_score,
                            }
                        )

                if not scored_entries:
                    continue

                scored_entries.sort(key=lambda item: item["score"], reverse=True)
                max_from_sentence = min(3, target_count - len(questions_data))

                for entry in scored_entries[:max_from_sentence]:
                    if len(questions_data) >= target_count:
                        break
                    if entry["pair_key"] in seen_pairs:
                        continue

                    seen_pairs.add(entry["pair_key"])
                    questions_data.append(
                        {
                            "question": entry["question"],
                            "answer": entry["answer"],
                            "sentence": entry["sentence"],
                        }
                    )

            if not questions_data:
                return "Error: Could not generate questions from the text."

            formatted_output = self._format_by_type(questions_data, quantities)
            if is_filipino_mode:
                formatted_output = self._translate_formatted_output_to_filipino(formatted_output)
            return formatted_output

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
        stop_words = self._get_stop_words()
        phrase_candidates = self._extract_phrase_candidates(sentence, stop_words)

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

        prioritized = time_phrases + phrase_candidates + proper_nouns + unique_candidates
        ordered_unique = []
        seen_all = set()
        for candidate in prioritized:
            lowered = candidate.lower()
            if lowered in seen_all:
                continue
            seen_all.add(lowered)
            ordered_unique.append(candidate)

        ranked = sorted(ordered_unique, key=lambda candidate: self._score_answer_candidate(candidate, sentence), reverse=True)
        return ranked[:5]

    def _generate_question_for_answer(self, sentence, answer):
        prompt = f"answer: {answer} context: {sentence} </s>"

        encoded_inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            max_length=256,
            truncation=True,
        )
        input_ids = encoded_inputs["input_ids"].to(self.device)
        attention_mask = encoded_inputs["attention_mask"].to(self.device)

        with torch.no_grad():
            outputs = self.model.generate(
                input_ids=input_ids,
                attention_mask=attention_mask,
                max_length=96,
                num_beams=4,
                do_sample=False,
                early_stopping=True,
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

        if not self._is_question_quality_acceptable(question, answer, sentence):
            return None

        return question

    def _format_by_type(self, questions_data, quantities):
        formatted = ""
        q_num = 1
        tf_created = 0
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

            normalized_question = selected_item["question"].strip().lower()
            used_question_texts.add(normalized_question)

            if question_type == "multiple_choice":
                options, answer_label = self._build_multiple_choice_options(selected_item)
                if not options or not answer_label:
                    formatted += f"{q_num}. {selected_item['question']}\n"
                    formatted += f"Answer: {selected_item['answer']}\n"
                    formatted += f"Context: {self._format_context(selected_item['sentence'])}\n\n"
                    q_num += 1
                    continue
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
                formatted += f"{q_num}. {selected_statement}\n"
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
                formatted += "Note: Manual checking required.\n"
                formatted += "\n"
                q_num += 1

        return formatted

    def _ensure_translation_resources(self, direction):
        if direction in self.translation_resources:
            return self.translation_resources[direction]

        model_name = self.translation_model_names[direction]
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        model.to(self.device)
        self.translation_resources[direction] = (tokenizer, model)
        return tokenizer, model

    def _translate_text(self, text, direction):
        cleaned_text = self._normalize_text(text)
        if not cleaned_text:
            return ""

        cache_key = (direction, cleaned_text)
        cached_value = self.translation_cache.get(cache_key)
        if cached_value is not None:
            return cached_value

        try:
            tokenizer, model = self._ensure_translation_resources(direction)
            encoded = tokenizer(
                cleaned_text,
                return_tensors="pt",
                max_length=512,
                truncation=True,
            )
            input_ids = encoded["input_ids"].to(self.device)
            attention_mask = encoded["attention_mask"].to(self.device)

            with torch.no_grad():
                generated = model.generate(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    max_length=256,
                    num_beams=4,
                    do_sample=False,
                    early_stopping=True,
                )

            translated = tokenizer.decode(generated[0], skip_special_tokens=True).strip()
            normalized_translated = self._normalize_text(translated)
            self.translation_cache[cache_key] = normalized_translated
            return normalized_translated
        except Exception as error:
            print(f"Translation warning ({direction}): {error}")
            self.translation_cache[cache_key] = cleaned_text
            return cleaned_text

    def _split_translation_chunks(self, text, max_chars=260):
        segments = [segment.strip() for segment in re.split(r"(?<=[.!?])\s+", text) if segment.strip()]
        if not segments:
            return [text] if text else []

        chunks = []
        current_chunk = ""

        for segment in segments:
            proposed = f"{current_chunk} {segment}".strip() if current_chunk else segment
            if len(proposed) <= max_chars:
                current_chunk = proposed
                continue

            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = segment

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def _translate_long_text(self, text, direction):
        normalized_text = self._normalize_text(text)
        if not normalized_text:
            return ""

        chunks = self._split_translation_chunks(normalized_text)
        translated_chunks = [self._translate_text(chunk, direction) for chunk in chunks]
        translated_chunks = [chunk for chunk in translated_chunks if chunk]
        translated_text = self._normalize_text(" ".join(translated_chunks))
        if direction == "en_tl":
            return self._normalize_filipino_spelling(translated_text)
        return translated_text

    def _translate_formatted_output_to_filipino(self, formatted_output):
        if not formatted_output.strip():
            return formatted_output

        translated_lines = []
        for line in formatted_output.splitlines():
            stripped_line = line.strip()
            if not stripped_line:
                translated_lines.append("")
                continue

            question_match = re.match(r"^(\d+\.\s+)(.+)$", stripped_line)
            if question_match:
                translated_question = self._translate_text(question_match.group(2), "en_tl")
                translated_question = self._normalize_filipino_spelling(translated_question)
                translated_lines.append(f"{question_match.group(1)}{translated_question}")
                continue

            choice_match = re.match(r"^([A-D]\)\s+)(.+)$", stripped_line)
            if choice_match:
                translated_choice = self._translate_text(choice_match.group(2), "en_tl")
                translated_choice = self._normalize_filipino_spelling(translated_choice)
                translated_lines.append(f"{choice_match.group(1)}{translated_choice}")
                continue

            if stripped_line.startswith("Context:"):
                context_value = stripped_line.split(":", 1)[1].strip()
                translated_context = self._translate_text(context_value, "en_tl")
                translated_context = self._normalize_filipino_spelling(translated_context)
                translated_lines.append(f"Context: {translated_context}")
                continue

            if stripped_line.startswith("Answer:"):
                answer_value = stripped_line.split(":", 1)[1].strip()
                answer_upper = answer_value.upper()
                answer_lower = answer_value.lower()

                if len(answer_upper) == 1 and answer_upper in {"A", "B", "C", "D"}:
                    translated_lines.append(f"Answer: {answer_upper}")
                    continue

                if answer_lower in {"true", "false"}:
                    translated_lines.append(f"Answer: {answer_value.title()}")
                    continue

                translated_answer = self._translate_text(answer_value, "en_tl")
                translated_answer = self._normalize_filipino_spelling(translated_answer)
                translated_lines.append(f"Answer: {translated_answer}")
                continue

            if stripped_line.lower() == "note: manual checking required.":
                translated_lines.append("Note: Kailangan ng manwal na pag-check.")
                continue

            translated_line = self._translate_text(stripped_line, "en_tl")
            translated_lines.append(self._normalize_filipino_spelling(translated_line))

        return "\n".join(translated_lines)

    def _normalize_filipino_spelling(self, text):
        normalized_text = self._normalize_text(text)
        if not normalized_text:
            return ""

        corrected_text = normalized_text
        for wrong_word, corrected_word in self.filipino_spelling_corrections.items():
            pattern = rf"\b{re.escape(wrong_word)}\b"
            corrected_text = re.sub(pattern, corrected_word, corrected_text, flags=re.IGNORECASE)

        corrected_text = re.sub(r"\s+-\s+", " - ", corrected_text)
        corrected_text = re.sub(r"\s+", " ", corrected_text).strip()
        return corrected_text

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

        cleaned_answer = self._clean_phrase(answer)
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
        stop_words = self._get_stop_words()
        phrase_candidates = self._extract_phrase_candidates(sentence, stop_words)
        words = re.findall(r"[A-Za-z][A-Za-z'\-]*", sentence)

        candidates = []
        for phrase in phrase_candidates:
            cleaned_phrase = self._clean_phrase(phrase)
            if not cleaned_phrase:
                continue
            if self._is_overlapping_answer(cleaned_phrase, correct_answer):
                continue
            if not self._is_valid_answer_candidate(cleaned_phrase):
                continue
            candidates.append(cleaned_phrase)

        for word in words:
            cleaned = self._clean_token(word).lower()
            if cleaned not in stop_words and cleaned != correct_answer.lower() and len(cleaned) > 2:
                candidate = self._clean_token(word)
                if not self._is_overlapping_answer(candidate, correct_answer) and self._is_valid_answer_candidate(candidate):
                    candidates.append(candidate)

        seen = set()
        unique = []
        for candidate in candidates:
            if candidate.lower() not in seen:
                seen.add(candidate.lower())
                unique.append(candidate)

        return unique[:count]

    def _build_multiple_choice_options(self, question_data):
        correct_answer = self._clean_phrase(question_data["answer"])
        if not correct_answer:
            correct_answer = self._clean_token(question_data["answer"])
        correct_token_count = self._token_count(correct_answer)

        correct_category = self._infer_entity_category(correct_answer)
        semantic_distractors = self._get_semantic_distractors(correct_answer, 4)
        context_distractors = self._get_distractors(question_data["sentence"], correct_answer, 12)
        distractors = semantic_distractors + context_distractors

        same_category_distractors = []
        other_distractors = []
        for distractor in distractors:
            cleaned = self._clean_phrase(distractor)
            if not cleaned:
                continue
            if cleaned.lower() == correct_answer.lower() or self._is_overlapping_answer(cleaned, correct_answer):
                continue

            if correct_token_count >= 2 and self._token_count(cleaned) < 2:
                continue

            if self._is_same_category(correct_category, self._infer_entity_category(cleaned)):
                same_category_distractors.append(cleaned)
            else:
                other_distractors.append(cleaned)

        unique_distractors = []
        seen = set()
        for distractor in same_category_distractors + other_distractors:
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
                if correct_token_count >= 2 and self._token_count(fallback_option) < 2:
                    continue
                seen.add(fallback_option.lower())
                unique_distractors.append(fallback_option)

        entity_fallbacks = self.entity_fallback_pools.get(correct_category, self.entity_fallback_pools["unknown"])
        for fallback_option in entity_fallbacks:
            if len(unique_distractors) >= 3:
                break
            cleaned_fallback = self._clean_phrase(fallback_option)
            if not cleaned_fallback:
                continue
            if cleaned_fallback.lower() == correct_answer.lower():
                continue
            if cleaned_fallback.lower() in seen:
                continue
            if self._is_overlapping_answer(cleaned_fallback, correct_answer):
                continue
            if correct_token_count >= 2 and self._token_count(cleaned_fallback) < 2:
                continue
            seen.add(cleaned_fallback.lower())
            unique_distractors.append(cleaned_fallback)

        if len(unique_distractors) < 3:
            question_words = re.findall(r"[A-Za-z][A-Za-z'\-]*", question_data.get("question", ""))
            stop_words = self._get_stop_words()
            for word in question_words:
                if len(unique_distractors) >= 3:
                    break
                cleaned_word = self._clean_token(word)
                lowered_word = cleaned_word.lower()
                if len(cleaned_word) < 4:
                    continue
                if lowered_word in stop_words or lowered_word in seen:
                    continue
                if lowered_word == correct_answer.lower() or self._is_overlapping_answer(cleaned_word, correct_answer):
                    continue
                if correct_token_count >= 2 and self._token_count(cleaned_word) < 2:
                    continue
                if not self._is_valid_answer_candidate(cleaned_word):
                    continue
                seen.add(lowered_word)
                unique_distractors.append(cleaned_word)

        if len(unique_distractors) < 3:
            return None, None

        options = [correct_answer] + unique_distractors[:3]

        self.random.shuffle(options)
        answer_index = options.index(correct_answer)
        answer_label = ["A", "B", "C", "D"][answer_index]
        formatted_options = [self._format_option_text(option) for option in options]

        return formatted_options, answer_label

    def _extract_phrase_candidates(self, sentence, stop_words):
        patterns = [
            r"\b(?:si|ni|kay|kina)\s+([A-Z][A-Za-z'\-]*(?:\s+[A-Z][A-Za-z'\-]*){0,3})",
            r"\b([A-Z]{2,}(?:\s+[A-Z]{2,}){1,4})\b",
            r"\b([A-Z][A-Za-z'\-]*(?:\s+[A-Z][A-Za-z'\-]*){1,4})\b",
            r"\b(?:a|an|the)\s+([A-Za-z][A-Za-z'\-]*\s+[A-Za-z][A-Za-z'\-]*)\b",
            r"\b(?:ang|ng|sa|mga)\s+([A-Za-z][A-Za-z'\-]*(?:\s+[A-Za-z][A-Za-z'\-]*){1,3})",
            r"\b((?:went|goes|go|turned|turns|became|becomes|grew|grow|fell|fall|looked|looks|seemed|seems)\s+[A-Za-z][A-Za-z'\-]*)\b",
        ]

        extracted = []
        seen = set()
        for pattern in patterns:
            for match in re.finditer(pattern, sentence):
                raw_phrase = match.group(1)
                phrase = self._clean_phrase(raw_phrase)
                lowered = phrase.lower()
                if not phrase or lowered in seen:
                    continue
                if self._looks_like_bad_noun_phrase(phrase):
                    continue
                if self._is_mostly_stop_words(phrase, stop_words):
                    continue
                if not self._is_valid_answer_candidate(phrase):
                    continue
                seen.add(lowered)
                extracted.append(phrase)

        return extracted

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
        cleaned = self._clean_phrase(candidate)
        lowered = cleaned.lower()
        if not cleaned:
            return False

        if re.fullmatch(r"\d+", lowered):
            return False

        tokens = re.findall(r"[A-Za-z0-9']+", lowered)
        if not tokens:
            return False

        if len(tokens) == 1 and len(tokens[0]) <= 2:
            return False

        if len(tokens) == 1 and (
            tokens[0] in self.weak_answer_words
            or tokens[0] in self.filipino_function_words
            or tokens[0] in self.low_value_answer_words
        ):
            return False

        if len(tokens) == 1 and (tokens[0].endswith("'s") or tokens[0].endswith("’s")):
            return False

        stop_words = self._get_stop_words()
        meaningful_tokens = [
            token
            for token in tokens
            if token not in stop_words and token not in self.weak_answer_words and token not in self.low_value_answer_words
        ]
        if not meaningful_tokens:
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

    def _infer_entity_category(self, answer):
        cleaned = self._clean_phrase(answer)
        lowered = cleaned.lower()
        tokens = re.findall(r"[A-Za-z0-9']+", cleaned)
        if not tokens:
            return "unknown"

        answer_type = self._infer_answer_type(cleaned)
        if answer_type in {"time_of_day", "duration", "frequency"}:
            return "time"
        if answer_type == "number":
            return "number"
        if answer_type == "direction":
            return "direction"
        if self._is_action_phrase(cleaned):
            return "action"

        person_markers = {"don", "dona", "doña", "mr", "mrs", "ms", "sir", "lady", "prince", "princess", "haring", "reyna"}
        place_markers = {"kingdom", "kaharian", "city", "lungsod", "village", "nayon", "forest", "gubat", "mountain", "bundok", "river", "ilog", "palace", "palasyo", "island", "pulo"}
        creature_markers = {"bird", "ibon", "dragon", "horse", "kabayo", "wolf", "lobo", "lion", "leon", "snake", "ahas", "adarna"}
        title_markers = {"story", "kuwento", "alamat", "epiko", "awit", "book", "novel", "poem"}

        if any(token in person_markers for token in re.findall(r"[A-Za-z']+", lowered)):
            return "person"

        if len(tokens) >= 2 and all(token and token[0].isupper() for token in cleaned.split() if token):
            return "person"

        if any(token in place_markers for token in re.findall(r"[A-Za-z']+", lowered)):
            return "place"

        if any(token in creature_markers for token in re.findall(r"[A-Za-z']+", lowered)):
            return "creature"

        if any(token in title_markers for token in re.findall(r"[A-Za-z']+", lowered)):
            return "title"

        if len(tokens) >= 2 and any(token and token[0].isupper() for token in cleaned.split()):
            return "title"

        return "object"

    def _is_same_category(self, expected, candidate):
        if expected == "unknown" or candidate == "unknown":
            return True

        if expected in {"time", "number", "direction", "person", "place", "creature", "action"}:
            return expected == candidate

        if expected == "title":
            return candidate in {"title", "object"}

        if expected == "object":
            return candidate in {"object", "title"}

        return expected == candidate

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

    def _clean_phrase(self, phrase):
        cleaned = self._normalize_text(phrase)
        cleaned = re.sub(r"^[^A-Za-z0-9]+|[^A-Za-z0-9]+$", "", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned.strip()

    def _token_count(self, text):
        return len(re.findall(r"[A-Za-z0-9']+", self._clean_phrase(text)))

    def _is_action_phrase(self, text):
        cleaned = self._clean_phrase(text).lower()
        return bool(
            re.search(
                r"\b(?:went|goes|go|turned|turns|became|becomes|grew|grow|fell|fall|looked|looks|seemed|seems)\s+[a-z][a-z'\-]*\b",
                cleaned,
            )
        )

    def _looks_like_bad_noun_phrase(self, text):
        cleaned = self._clean_phrase(text).lower()
        tokens = re.findall(r"[A-Za-z0-9']+", cleaned)
        if len(tokens) < 2:
            return False

        title_markers = {"story", "tale", "legend", "book", "chapter", "article", "passage", "kuwento", "alamat", "epiko"}
        if tokens[0] in title_markers:
            second_token = tokens[1]
            if (
                second_token in self.common_verb_tokens
                or second_token.endswith("ed")
                or second_token.endswith("ing")
            ):
                return True

        if self._is_action_phrase(cleaned):
            return False

        return tokens[-1] in self.common_verb_tokens

    def _is_mostly_stop_words(self, text, stop_words):
        tokens = re.findall(r"[A-Za-z0-9']+", text.lower())
        if not tokens:
            return True
        meaningful = [token for token in tokens if token not in stop_words and token not in self.weak_answer_words]
        return len(meaningful) == 0

    def _is_overlapping_answer(self, candidate, answer):
        candidate_clean = self._clean_phrase(candidate).lower()
        answer_clean = self._clean_phrase(answer).lower()
        if not candidate_clean or not answer_clean:
            return False

        if candidate_clean == answer_clean:
            return True
        if candidate_clean in answer_clean or answer_clean in candidate_clean:
            return True

        stop_words = self._get_stop_words()
        candidate_tokens = {token for token in re.findall(r"[A-Za-z0-9']+", candidate_clean) if token not in stop_words}
        answer_tokens = {token for token in re.findall(r"[A-Za-z0-9']+", answer_clean) if token not in stop_words}
        if not candidate_tokens or not answer_tokens:
            return False

        overlap = candidate_tokens.intersection(answer_tokens)
        if not overlap:
            return False

        overlap_ratio = len(overlap) / min(len(candidate_tokens), len(answer_tokens))
        return overlap_ratio >= 0.8

    def _format_option_text(self, text):
        cleaned = self._clean_phrase(text)
        if not cleaned:
            return text

        if re.fullmatch(r"[A-Z\s\-']+", cleaned) and len(cleaned) > 3:
            return " ".join(part.capitalize() if part else part for part in cleaned.split(" "))

        return cleaned

    def _get_stop_words(self):
        english_stop_words = {
            "is", "are", "was", "were", "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "be", "been", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "must", "can", "it", "that", "this", "which", "who",
            "what", "when", "where", "why", "how", "there", "their", "then", "than", "very", "just", "while",
            "after", "before", "during", "since", "until", "every", "as", "into", "onto", "up", "down", "out",
            "about"
        }
        return english_stop_words.union(self.filipino_function_words)

    def _is_sentence_informative(self, sentence):
        stop_words = self._get_stop_words()
        tokens = [token for token in re.findall(r"[A-Za-z0-9']+", sentence.lower()) if token not in stop_words]
        meaningful_tokens = [
            token for token in tokens if token not in self.weak_answer_words and token not in self.low_value_answer_words
        ]

        if len(meaningful_tokens) < 5:
            return False

        phrase_candidates = self._extract_phrase_candidates(sentence, stop_words)
        if phrase_candidates:
            return True

        if re.search(r"\b\d+\b", sentence):
            return True

        return len(meaningful_tokens) >= 7

    def _score_answer_candidate(self, answer, sentence):
        cleaned = self._clean_phrase(answer)
        lowered = cleaned.lower()
        tokens = re.findall(r"[A-Za-z0-9']+", cleaned)
        if not tokens:
            return -1000

        score = 0
        score += min(len(tokens), 4) * 2

        if len(tokens) >= 2:
            score += 3

        if any(token and token[0].isupper() for token in cleaned.split()):
            score += 2

        entity_category = self._infer_entity_category(cleaned)
        if entity_category in {"person", "place", "creature", "title"}:
            score += 3
        if entity_category == "action":
            score += 4

        if lowered in self.low_value_answer_words:
            score -= 8

        if len(tokens) == 1 and tokens[0] in self.weak_answer_words:
            score -= 6

        if lowered in sentence.lower():
            score += 1

        return score

    def _score_question_candidate(self, question, answer, sentence):
        question_tokens = re.findall(r"[A-Za-z0-9']+", question.lower())
        answer_tokens = re.findall(r"[A-Za-z0-9']+", self._clean_phrase(answer).lower())
        stop_words = self._get_stop_words()

        score = 0
        score += min(len(question_tokens), 12)
        score += self._score_answer_candidate(answer, sentence)

        if question.lower().startswith(("who", "what", "where", "when", "why", "how")):
            score += 2

        content_tokens = [token for token in question_tokens if token not in stop_words]
        if len(content_tokens) < 4:
            score -= 8

        sentence_tokens = re.findall(r"[A-Za-z0-9']+", sentence.lower())
        overlap_with_sentence = len(set(question_tokens).intersection(set(sentence_tokens)))
        if overlap_with_sentence > max(8, len(question_tokens) * 0.8):
            score -= 6

        if answer_tokens and all(token in question_tokens for token in answer_tokens):
            score -= 10

        return score

    def _is_question_quality_acceptable(self, question, answer, sentence):
        lowered = question.lower().strip()
        content_tokens = [token for token in re.findall(r"[A-Za-z0-9']+", lowered) if token not in self._get_stop_words()]

        if len(content_tokens) < 4:
            return False

        if lowered.startswith("what did everyone"):
            return False

        if lowered.startswith("what is that") or lowered.startswith("what is this"):
            return False

        if self._score_question_candidate(question, answer, sentence) < 4:
            return False

        return True

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
