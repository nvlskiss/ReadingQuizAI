#!/usr/bin/env python
"""Test script to verify T5 model and FairytaleQA integration"""

print("Testing T5 model loading...")
try:
    from question_generator import QuestionGenerator
    print("✓ Imported QuestionGenerator")
except Exception as e:
    print(f"✗ Error importing QuestionGenerator: {e}")
    exit(1)

print("\nTesting FairytaleQA handler loading...")
try:
    from fairytale_qa_handler import FairytaleQAHandler
    print("✓ Imported FairytaleQAHandler")
except Exception as e:
    print(f"✗ Error importing FairytaleQAHandler: {e}")
    exit(1)

print("\nInitializing T5 model (this may take a moment)...")
try:
    generator = QuestionGenerator()
    print("✓ T5 model loaded successfully")
except Exception as e:
    print(f"✗ Error loading T5 model: {e}")
    exit(1)

print("\nInitializing FairytaleQA handler...")
try:
    fairytale_handler = FairytaleQAHandler("fairytale_qa_data")
    print("✓ FairytaleQA handler initialized")
    if fairytale_handler.is_fairytale_dataset_available():
        print(f"  └─ Dataset loaded with {len(fairytale_handler.stories)} stories")
    else:
        print("  └─ Dataset not found (will work with standard grading)")
except Exception as e:
    print(f"✗ Error with FairytaleQA handler: {e}")
    exit(1)

print("\n✓ All components loaded successfully!")
print("\nTesting question generation with simple example...")
try:
    text = "The sun rises in the east and sets in the west. It provides light and warmth for all living things."
    question_types = {"multiple_choice": 1}
    
    print(f"Input text: '{text}'")
    print(f"Generating: {question_types}")
    
    result = generator.generate_questions(text, question_types, question_types)
    print(f"\nGenerated output (first 300 chars):")
    print(result[:300])
    print("\n✓ Question generation test successful!")
    
except Exception as e:
    print(f"✗ Error generating questions: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "="*50)
print("ALL TESTS PASSED!")
print("Your application is ready to use with:")
print("  • Fine-tuned T5 model for question generation")
print("  • FairytaleQA dataset for smart answer grading")
print("="*50)
