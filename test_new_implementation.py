from question_generator import QuestionGenerator
from quiz_parser import QuizParser

gen = QuestionGenerator()

test_text = '''In a small house on Mango Street, Esperanza lived with her family. One night, a golden lantern hung in the window. The lantern shone brightly, casting warm light. Esperanza remembered the lantern from her childhood dreams.'''

print('Generating questions...')
questions_text = gen.generate_questions(test_text, [], {
    'multiple_choice': 1,
    'true_or_false': 1,
    'identification': 1
})

print('Raw output from model:')
print('='*80)
print(questions_text[:800])
print('='*80)

print('\n\nParsing questions...')
parsed = QuizParser.parse_questions(questions_text)

print('Successfully parsed {} questions:\n'.format(len(parsed)))
for i, q in enumerate(parsed, 1):
    print('{}. [{}] {}'.format(i, q['type'].upper(), q['question']))
    if 'options' in q:
        for j, opt in enumerate(q['options'], 1):
            letter = chr(64 + j)  # A, B, C, D
            print('   {}) {}'.format(letter, opt))
    print('   Correct Answer: {}'.format(q['answer']))
    print()
