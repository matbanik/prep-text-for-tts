#!/usr/bin/env python3
"""
Detailed analysis of differences between PROCESSED_OUTPUT.txt and OUTPUT.txt
"""

from pathlib import Path
import difflib

def analyze_differences():
    # Get repo root
    repo_root = Path(__file__).parent.parent
    processed = (repo_root / "PROCESSED_OUTPUT.txt").read_text()
    expected = (repo_root / "docs" / "OUTPUT.txt").read_text()

    processed_lines = processed.split('\n')
    expected_lines = expected.split('\n')

    print(f"PROCESSED: {len(processed_lines)} lines")
    print(f"EXPECTED:  {len(expected_lines)} lines")
    print(f"DIFFERENCE: {len(processed_lines) - len(expected_lines)} lines")
    print("\n" + "="*80 + "\n")

    # Get detailed diff
    matcher = difflib.SequenceMatcher(None, expected_lines, processed_lines)

    diff_count = 0
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            continue

        diff_count += 1
        print(f"\n[DIFF #{diff_count}] {tag.upper()}: Expected lines {i1+1}-{i2} vs Actual lines {j1+1}-{j2}")
        print("-" * 80)

        if tag == 'delete':
            print("MISSING IN ACTUAL:")
            for i in range(i1, i2):
                line = expected_lines[i]
                display = line[:75] + "..." if len(line) > 75 else line
                print(f"  {i+1:3}: {repr(display)}")

        elif tag == 'insert':
            print("EXTRA IN ACTUAL:")
            for j in range(j1, j2):
                line = processed_lines[j]
                display = line[:75] + "..." if len(line) > 75 else line
                print(f"  {j+1:3}: {repr(display)}")

        elif tag == 'replace':
            print("EXPECTED:")
            for i in range(i1, i2):
                line = expected_lines[i]
                display = line[:75] + "..." if len(line) > 75 else line
                print(f"  {i+1:3}: {repr(display)}")
            print("\nACTUAL:")
            for j in range(j1, j2):
                line = processed_lines[j]
                display = line[:75] + "..." if len(line) > 75 else line
                print(f"  {j+1:3}: {repr(display)}")

            # Show character-level diff for replace
            if i2 - i1 == 1 and j2 - j1 == 1:
                exp_line = expected_lines[i1]
                act_line = processed_lines[j1]

                # Find differences
                sm = difflib.SequenceMatcher(None, exp_line, act_line)
                print("\nCHARACTER-LEVEL DIFFERENCES:")
                for tag2, i3, i4, j3, j4 in sm.get_opcodes():
                    if tag2 != 'equal':
                        print(f"  {tag2}: pos {i3}-{i4} '{exp_line[i3:i4]}' → '{act_line[j3:j4]}'")

if __name__ == "__main__":
    analyze_differences()
