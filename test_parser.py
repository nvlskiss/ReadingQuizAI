#!/usr/bin/env python
"""Quick test of parser with T5-like output"""

from quiz_parser import QuizParser

# Simulated T5 output
test_output = """1. What is the answer to this question based on the text?
A) First option
B) Second option  
C) Third option
D) Fourth option
Answer: B

2. Is this statement true or false based on the text?
Answer: True

3. What is the answer?
Answer: Short answer"""

print("Testing parser with simulated T5 output...")
print("="*60)
print("Input:")
print(test_output)
print("="*60)

questions = QuizParser.parse_questions(test_output)

print(f"\nParsed {len(questions)} questions:")
for i, q in enumerate(questions, 1):
    print(f"\n{i}. Type: {q['type']}")
    print(f"   Question: {q['question'][:60]}...")
    if 'options' in q:
        print(f"   Options: {len(q['options'])} options")
    print(f"   Answer: {q.get('answer', 'N/A')}")

if len(questions) == 0:
    print("\n✗ Parser failed to extract questions!")
else:
    print(f"\n✓ Parser successfully extracted {len(questions)} questions!")
