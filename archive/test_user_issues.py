#!/usr/bin/env python3
"""Test fixes for user-reported issues"""

import re
from pathlib import Path

def fix_orphaned_apostrophes(text):
    text = re.sub(r"(\w+)'\s*\n?\s*([a-z])", r"\1 \2", text)
    text = re.sub(r"'(\s*\n\s*)([a-z])", r"\1\2", text)
    return text

def fix_split_words(text):
    """
    Fix only TRUE split words (word fragments across lines).

    Strategy:
    1. Always fix hyphenated breaks (unambiguous)
    2. For non-hyphenated: Only merge if first part is NOT a common complete word
    """
    # Fix hyphenated line breaks (always merge)
    text = re.sub(r'(\w+)-\s*\n\s*(\w+)', lambda m: m.group(1) + m.group(2), text)

    # Common complete English words that should NOT be merged with next line
    # (These are complete words, not fragments)
    COMPLETE_WORDS = {
        'a', 'an', 'the', 'and', 'or', 'but', 'if', 'of', 'to', 'in', 'on', 'at', 'by',
        'for', 'with', 'from', 'up', 'out', 'as', 'is', 'are', 'was', 'were', 'be',
        'he', 'she', 'it', 'we', 'they', 'you', 'i', 'me', 'him', 'her', 'us', 'them',
        'his', 'her', 'its', 'our', 'their', 'my', 'your', 'this', 'that', 'these', 'those',
        'all', 'some', 'any', 'many', 'much', 'more', 'most', 'own', 'can', 'will', 'would',
        'could', 'should', 'may', 'might', 'must', 'shall', 'do', 'does', 'did', 'have',
        'has', 'had', 'who', 'what', 'when', 'where', 'why', 'how', 'than', 'then', 'now',
        'so', 'not', 'no', 'yes', 'like', 'just', 'part', 'make', 'get', 'go', 'come',
        'take', 'see', 'know', 'think', 'look', 'want', 'give', 'use', 'find', 'tell',
        'ask', 'work', 'seem', 'feel', 'try', 'leave', 'call', 'even', 'also', 'only',
        'new', 'good', 'old', 'great', 'first', 'last', 'long', 'little', 'such', 'other',
        'between', 'under', 'over', 'through', 'during', 'before', 'after', 'above', 'below',
        'both', 'each', 'few', 'every', 'either', 'neither', 'whether', 'because', 'since',
        'while', 'until', 'unless', 'though', 'although', 'even', 'still', 'yet', 'already'
    }

    def merge_if_fragment(match):
        first_part = match.group(1)
        second_part = match.group(2)

        # Don't merge if first part is a known complete word
        if first_part.lower() in COMPLETE_WORDS:
            return match.group(0)  # Keep newline

        # Merge if first part appears to be a word fragment
        return first_part + second_part

    text = re.sub(r'(\w+)\n(\w+)', merge_if_fragment, text)

    return text

def merge_sentence_lines(text):
    """
    Merge lines within sentences (preserving paragraph breaks).

    Strategy: Don't use placeholder - instead track paragraph breaks
    and don't merge across them.
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

def test_fixes():
    test_file = Path("TEST_USER_ISSUES.txt")
    if not test_file.exists():
        print(f"Error: {test_file} not found!")
        return

    print("="*90)
    print(" "*30 + "USER ISSUE FIXES TEST")
    print("="*90)
    print()

    with open(test_file, 'r', encoding='utf-8') as f:
        original_text = f.read()

    print("📖 ORIGINAL TEXT (with issues):")
    print("-"*90)
    print(original_text[:500] + "..." if len(original_text) > 500 else original_text)
    print("-"*90)
    print()

    # Test each fix
    print("🔧 APPLYING FIXES:")
    print()

    # Fix 1: Orphaned apostrophes
    print("1️⃣  Fixing orphaned apostrophes (people'and → people and)")
    before_len = len(original_text)
    step1 = fix_orphaned_apostrophes(original_text)
    after_len = len(step1)
    changes = before_len - after_len
    print(f"   Removed {changes} characters")
    print()

    # Fix 2: Split words
    print("2️⃣  Fixing split words (hun\\ndred → hundred)")
    before_len = len(step1)
    step2 = fix_split_words(step1)
    after_len = len(step2)
    changes = before_len - after_len
    print(f"   Removed {changes} characters (merged {changes} line breaks)")
    print()

    # Fix 3: Merge sentence lines
    print("3️⃣  Merging mid-sentence newlines")
    before_len = len(step2)
    final_text = merge_sentence_lines(step2)
    after_len = len(final_text)
    changes = before_len - after_len
    print(f"   Removed {changes} characters (merged lines)")
    print()

    print("="*90)
    print("✅ FIXED TEXT:")
    print("="*90)
    print(final_text)
    print()
    print("="*90)

    # Save result
    output_file = Path("TEST_USER_ISSUES_FIXED.txt")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(final_text)

    print(f"✓ Saved to: {output_file}")
    print(f"   Original: {len(original_text):,} chars")
    print(f"   Fixed:    {len(final_text):,} chars")
    print(f"   Removed:  {len(original_text) - len(final_text):,} chars")
    print()

    # Check for specific issues
    print("🔍 VERIFICATION:")
    if "people'and" in final_text:
        print("   ❌ Still has: people'and")
    else:
        print("   ✅ Fixed: people'and → people and")

    if "me'from" in final_text:
        print("   ❌ Still has: me'from")
    else:
        print("   ✅ Fixed: me'from → me from")

    if "hun\ndred" in final_text:
        print("   ❌ Still has: hun\\ndred")
    else:
        print("   ✅ Fixed: hun\\ndred → hundred")

    if "sur\nvival" in final_text:
        print("   ❌ Still has: sur\\nvival")
    else:
        print("   ✅ Fixed: sur\\nvival → survival")

    # Count mid-sentence newlines (heuristic)
    lines = final_text.split('\n')
    mid_sentence_breaks = sum(1 for line in lines if line and not re.search(r'[.!?]\s*$', line.strip()))
    print(f"   ℹ️  Remaining mid-sentence breaks: {mid_sentence_breaks}")

if __name__ == "__main__":
    test_fixes()
