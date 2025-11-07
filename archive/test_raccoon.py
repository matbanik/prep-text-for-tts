#!/usr/bin/env python3
"""Test the raccoon text preprocessing."""

from pathlib import Path
import re
import ftfy
import spacy

# Load spaCy model
try:
    nlp = spacy.load('en_core_web_sm')
except OSError:
    print("Downloading spaCy model...")
    import subprocess
    subprocess.run(['python', '-m', 'spacy', 'download', 'en_core_web_sm'])
    nlp = spacy.load('en_core_web_sm')

# Import just the functions we need from tts_preprocessor_gui
# Copy the functions directly since we can't import the GUI module
def merge_sentence_lines(text):
    """
    Merge lines within sentences (preserving paragraph breaks).
    """
    lines = text.split('\n')
    merged_lines = []
    i = 0

    while i < len(lines):
        current_line = lines[i].rstrip()

        # Check if this is a blank line (paragraph separator) - keep it as-is
        if not current_line.strip():
            merged_lines.append(current_line)
            i += 1
            continue

        # Check if this line ends with sentence-ending punctuation
        ends_with_punctuation = bool(re.search(r'[.!?;]\s*["\']?\s*$', current_line))

        # If not ending punctuation and there's a next line, try to merge
        if not ends_with_punctuation and i + 1 < len(lines):
            next_line = lines[i + 1].lstrip()

            # Don't merge if next line is empty (paragraph break)
            if not next_line:
                merged_lines.append(current_line)
                i += 1
                continue

            # Only merge if next line doesn't start with capital
            if not next_line[0].isupper():
                merged_lines.append(current_line + ' ' + next_line)
                i += 2
                continue

        merged_lines.append(current_line)
        i += 1

    return '\n'.join(merged_lines)

def test_raccoon():
    test_file = Path("TEST_RACCOON.txt")
    original_text = test_file.read_text()

    print("="*90)
    print("TESTING RACCOON TEXT PREPROCESSING")
    print("="*90)
    print()

    # Show first 500 chars of original
    print("📖 ORIGINAL TEXT (first 500 chars):")
    print("-"*90)
    print(original_text[:500])
    print("...")
    print("-"*90)
    print()

    # Test merge_sentence_lines specifically
    print("Testing merge_sentence_lines():")
    print("-"*90)

    # Show a problematic section
    problematic = """I took my knife from my sheath and finding a charred stick, began to whittle away at the charcoal.
My
whittling worked into an intense hacking."""

    print("BEFORE merge_sentence_lines:")
    print(repr(problematic))
    print()

    result = merge_sentence_lines(problematic)
    print("AFTER merge_sentence_lines:")
    print(repr(result))
    print()

    # Show formatted
    print("FORMATTED:")
    print(result)
    print("-"*90)
    print()

    # Run full preprocessing (just merge_sentence_lines for now)
    print("Running merge_sentence_lines on full text...")
    print()

    processed = merge_sentence_lines(original_text)

    # Save result
    output_file = Path("TEST_RACCOON_FIXED.txt")
    output_file.write_text(processed)

    print("="*90)
    print("✅ PROCESSED TEXT (first 1000 chars):")
    print("="*90)
    print(processed[:1000])
    print("...")
    print()

    print(f"✓ Saved to: {output_file}")
    print(f"   Original: {len(original_text)} chars")
    print(f"   Processed: {len(processed)} chars")
    print()

    # Check for specific issues
    print("🔍 CHECKING FOR ISSUES:")
    print("-"*90)

    issues = []

    # Check for merged words (no space between)
    merged_words = [
        'beenkilled', 'becamelabored', 'racedthrough', 'intothe', 'lifethat',
        'enoughand', 'ashesand', 'teethand', 'headin', 'windand', 'somethingsoft',
        'emptinessslowly', 'fallafternoon', 'Wolfadded', 'Wolfswords', 'streamsand',
        'turnstones', 'laughedwhen', 'questioninglooks', 'thinkingof', 'lefther',
        'survivethe', 'StalkingWolf', 'didn thave', 'holedug'
    ]

    for word in merged_words:
        if word in processed:
            issues.append(f"❌ Still has merged word: {word}")

    # Check for orphan lines (single capital letter lines)
    lines = processed.split('\n')
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped and len(stripped) <= 3 and stripped[0].isupper():
            # Check if it's a standalone word (not part of merged sentence)
            if i + 1 < len(lines) and lines[i+1].strip():
                next_line = lines[i+1].strip()
                if next_line and next_line[0].islower():
                    issues.append(f"❌ Orphan line {i}: '{stripped}' (next: '{next_line[:30]}...')")

    if issues:
        print("\n".join(issues))
    else:
        print("✅ All checks passed!")

    print("-"*90)

if __name__ == "__main__":
    test_raccoon()
