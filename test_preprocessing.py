#!/usr/bin/env python3
"""Test the new TextPreprocessor with comprehensive logging"""

import sys
from pathlib import Path

# Import the TextPreprocessor
from tts_preprocessor_gui import TextPreprocessor

def test_preprocessing():
    """Test the preprocessing pipeline"""

    # Read test file
    test_file = Path("TEST_INPUT.txt")
    if not test_file.exists():
        print(f"Error: {test_file} not found!")
        return

    print("="*80)
    print("TESTING NEW TEXT PREPROCESSOR")
    print("="*80)
    print()

    with open(test_file, 'r', encoding='utf-8') as f:
        original_text = f.read()

    print(f"📖 Original text:")
    print(f"   Size: {len(original_text):,} chars")
    print(f"   Lines: {original_text.count(chr(10)) + 1}")
    print()

    # Test each step individually
    steps = [
        ("1. Clean Unicode (ftfy)", TextPreprocessor.clean_unicode),
        ("2. Remove Page Numbers", TextPreprocessor.remove_page_numbers),
        ("3. Fix Hyphenated Breaks", TextPreprocessor.fix_hyphenated_breaks),
        ("4. Normalize Whitespace", TextPreprocessor.normalize_whitespace),
        ("5. Chunk for TTS (spaCy)", lambda t: TextPreprocessor.chunk_for_tts(t, 250)),
    ]

    current_text = original_text

    for step_name, step_func in steps:
        before_size = len(current_text)
        current_text = step_func(current_text)
        after_size = len(current_text)
        change = after_size - before_size
        change_pct = (change / before_size * 100) if before_size > 0 else 0

        print(f"✓ {step_name}")
        print(f"   Before: {before_size:,} chars")
        print(f"   After:  {after_size:,} chars")
        print(f"   Change: {change:+,} chars ({change_pct:+.2f}%)")
        print()

    # Show final result
    print("="*80)
    print("FINAL RESULT:")
    print("="*80)
    print(current_text)
    print()
    print("="*80)

    # Save result
    output_file = Path("TEST_OUTPUT.txt")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(current_text)

    print(f"✓ Saved to: {output_file}")
    print(f"   Original: {len(original_text):,} chars")
    print(f"   Final:    {len(current_text):,} chars")
    print(f"   Change:   {len(current_text) - len(original_text):+,} chars")

    # Verify no major data loss
    data_loss_pct = ((len(original_text) - len(current_text)) / len(original_text)) * 100
    if data_loss_pct > 5:
        print(f"⚠️  WARNING: Data loss {data_loss_pct:.1f}%!")
    else:
        print(f"✓ Data integrity OK (loss: {data_loss_pct:.2f}%)")

if __name__ == "__main__":
    test_preprocessing()
