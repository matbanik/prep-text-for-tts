#!/usr/bin/env python3
"""Test the full preprocessing pipeline on raccoon text."""

from pathlib import Path
import re
import ftfy

# Copy the functions we need directly since we can't import the GUI module

def remove_page_headers(text):
    """Remove OCR page headers/footers that interrupt text flow."""
    lines = text.split('\n')
    cleaned_lines = []
    i = 0

    while i < len(lines):
        line = lines[i].strip()
        is_page_header = False

        if line:
            # Pattern 1: "Chapter Name/Number" or "Number/Chapter Name"
            if re.match(r'^[A-Za-z\s]+/\d+$', line) or re.match(r'^\d+/[A-Za-z\s]+$', line):
                is_page_header = True
            # Pattern 2: Standalone numbers (page numbers)
            elif re.match(r'^\d+$', line) and len(line) <= 4:
                is_page_header = True
            # Pattern 3: Very short lines between blank lines (likely headers)
            elif len(line) <= 25 and i > 0 and i < len(lines) - 1:
                prev_blank = (i == 0 or not lines[i-1].strip())
                next_blank = (i == len(lines) - 1 or not lines[i+1].strip())
                if prev_blank and next_blank:
                    if '/' in line or (any(c.isdigit() for c in line) and len(line.split()) <= 3):
                        is_page_header = True

        if not is_page_header:
            cleaned_lines.append(lines[i])
        else:
            print(f"   [REMOVED PAGE HEADER]: {repr(line)}")

            # Page header found - also skip surrounding blank lines
            # Remove preceding blank line if it exists
            if cleaned_lines and not cleaned_lines[-1].strip():
                cleaned_lines.pop()
                print(f"   [REMOVED PRECEDING BLANK LINE]")

            # Skip following blank line
            if i + 1 < len(lines) and not lines[i + 1].strip():
                i += 1
                print(f"   [SKIPPED FOLLOWING BLANK LINE]")

        i += 1

    return '\n'.join(cleaned_lines)

def fix_merged_words(text):
    """Fix OCR errors where two words are merged without a space."""
    WORD_PATTERNS = [
        # Verb past tense + article/preposition
        (r'\b(\w+ed)(the|and|that|when|with|from|by|in|to|at|on|through|into)\b', r'\1 \2'),
        # Verb -ing form + article/preposition
        (r'\b(\w+ing)(the|and|that|when|with|from|by|in|to|at|on|through|of|looks)\b', r'\1 \2'),
        # Been/had/was/were/became + past participle or adjective
        (r'\b(been|had|was|were|became)([a-z]{5,})\b', r'\1 \2'),
        # Verb + through/around/about/across
        (r'\b([a-z]+ed)(through|around|about|across|between|without)\b', r'\1 \2'),
        # Noun/verb + that/when/where
        (r'\b([a-z]{4,})(that|when|where|while|until|unless|though|since)\b', r'\1 \2'),
        # Preposition + article/pronoun
        (r'\b(in|on|at|to|of|for|with|from|by|into|onto)(the|a|an|my|his|her|their|our)\b', r'\1 \2'),
        # Common words + and
        (r'\b([a-z]{3,})(and)\b', r'\1 \2'),
        # Adjective/adverb patterns
        (r'\b([a-z]{4,})(slowly|quickly|quietly|loudly|softly|gently)\b', r'\1 \2'),
        # Specific common merged words only (not general pattern)
        (r'\b(head|hand|face|eyes|ears|mind|time|place|side|end)(of)\b', r'\1 \2'),
        # Word ending in consonant + afternoon/evening/morning
        (r'\b([a-z]+[bcdfghjklmnpqrstvwxz])(afternoon|evening|morning)\b', r'\1 \2'),
        # Proper names + added/said/asked/replied
        (r'\b([A-Z][a-z]+)(added|said|asked|replied|answered|continued)\b', r'\1 \2'),
        # Specific verb + her/him/them patterns (not general)
        (r'\b(left|told|gave|sent|showed|brought)(her|him|them)\b', r'\1 \2'),
        # Common word endings + soft/hard/long/short
        (r'\b([a-z]{4,})(soft|hard|long|short|big|small)\b', r'\1 \2'),
        # didn't/couldn't/wouldn't fix (apostrophe spacing)
        (r"\b(didn|couldn|wouldn|shouldn|haven|hasn|isn|wasn|weren|don|doesn)\s+t\s+([a-z]+)\b", r"\1't \2"),
        # survive/escape/return + the
        (r'\b(survive|escape|return|remain|become|explore|discover)(the)\b', r'\1 \2'),
        # Turn/pull/push/grab + noun
        (r'\b(turn|pull|push|grab|take|make|give)(stones|rocks|sticks|logs)\b', r'\1 \2'),
        # Head/hand/face/body + in/on/at
        (r'\b(head|hand|face|body|arm|leg)(in|on|at|to)\b', r'\1 \2'),
        # Word + words/days/years/things
        (r'\b([A-Z][a-z]+)(words|days|years|things)\b', r'\1 \2'),
    ]

    changes = 0
    for pattern, replacement in WORD_PATTERNS:
        new_text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        if new_text != text:
            changes += 1
        text = new_text

    print(f"   Applied {changes} merged word fix patterns")
    return text

def merge_sentence_lines(text):
    """Merge lines within sentences (preserving paragraph breaks)."""
    # First, convert double+ blank lines to a marker
    text = re.sub(r'\n\n+', '\n<<PARAGRAPH>>\n', text)

    lines = text.split('\n')
    merged_lines = []
    i = 0
    merge_count = 0

    while i < len(lines):
        current_line = lines[i].rstrip()

        # Check if this is the paragraph marker
        if current_line == '<<PARAGRAPH>>':
            # Convert back to double newline
            if merged_lines and merged_lines[-1]:  # Don't add if previous line is already blank
                merged_lines.append('')  # Add blank line for paragraph break
            i += 1
            continue

        # Skip truly empty lines (single blanks that aren't paragraph markers)
        if not current_line.strip():
            i += 1
            continue

        # Check if this line ends with sentence-ending punctuation
        ends_with_punctuation = bool(re.search(r'[.!?;]\s*["\']?\s*$', current_line))

        # If not ending punctuation, try to merge with next non-empty line
        if not ends_with_punctuation:
            # Look ahead for next non-empty line
            j = i + 1
            while j < len(lines) and (not lines[j].strip() or lines[j].strip() == '<<PARAGRAPH>>'):
                # Stop if we hit a paragraph marker
                if lines[j].strip() == '<<PARAGRAPH>>':
                    break
                j += 1

            if j < len(lines) and lines[j].strip() and lines[j].strip() != '<<PARAGRAPH>>':
                next_line = lines[j].lstrip()
                # Only merge if next line doesn't start with capital
                if not next_line[0].isupper():
                    merged_lines.append(current_line + ' ' + next_line)
                    merge_count += 1
                    i = j + 1
                    continue

        merged_lines.append(current_line)
        i += 1

    print(f"   Merged {merge_count} sentence lines")
    return '\n'.join(merged_lines)

def test_raccoon_full():
    test_file = Path("TEST_RACCOON.txt")
    original_text = test_file.read_text()

    print("="*90)
    print("FULL PREPROCESSING TEST ON RACCOON TEXT")
    print("="*90)
    print()

    print("📖 ORIGINAL TEXT STATS:")
    print(f"   Length: {len(original_text)} chars")
    print(f"   Lines: {original_text.count(chr(10)) + 1}")
    print()

    # Step 1: Remove page headers
    print("🔧 Step 1: Removing page headers...")
    step1 = remove_page_headers(original_text)
    print(f"   Removed: {len(original_text) - len(step1)} chars")
    print()

    # Step 2: Fix merged words
    print("🔧 Step 2: Fixing merged words...")
    step2 = fix_merged_words(step1)
    print(f"   Added spaces: {len(step2) - len(step1)} chars")
    print()

    # Step 3: Merge sentence lines
    print("🔧 Step 3: Merging sentence lines...")
    final = merge_sentence_lines(step2)
    print(f"   Removed newlines: {len(step2) - len(final)} chars")
    print()

    # Save result
    output_file = Path("TEST_RACCOON_FULL_FIXED.txt")
    output_file.write_text(final)

    print("="*90)
    print("✅ PROCESSED TEXT (first 2000 chars):")
    print("="*90)
    print(final[:2000])
    print("...")
    print()

    print(f"✓ Saved to: {output_file}")
    print(f"   Original: {len(original_text):,} chars")
    print(f"   Final:    {len(final):,} chars")
    print(f"   Change:   {len(final) - len(original_text):+,} chars")
    print()

    # Check for specific issues
    print("🔍 CHECKING FOR REMAINING ISSUES:")
    print("-"*90)

    issues = []
    merged_words = [
        'beenkilled', 'becamelabored', 'racedthrough', 'intothe', 'lifethat',
        'enoughand', 'ashesand', 'teethand', 'headin', 'windand', 'somethingsoft',
        'emptinessslowly', 'fallafternoon', 'Wolfadded', 'Wolfswords', 'streamsand',
        'turnstones', 'laughedwhen', 'questioninglooks', 'thinkingof', 'lefther',
        'survivethe'
    ]

    for word in merged_words:
        if word in final:
            issues.append(f"❌ Still has: {word}")

    if issues:
        print("\n".join(issues))
    else:
        print("✅ All merged word issues fixed!")

    # Check for page headers
    if 'Raccoon Encounter' in final or 'Tests and Encounters' in final:
        print("❌ Still has page headers!")
    else:
        print("✅ All page headers removed!")

    print("-"*90)

if __name__ == "__main__":
    test_raccoon_full()
