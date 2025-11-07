#!/usr/bin/env python3
"""
Quick script to check GUI version and button presence
"""

import re

# Read the GUI file
with open('tts_preprocessor_gui.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Check for Pre-clean button
if 'preclean_btn' in content:
    print("✅ Pre-clean button code IS present in tts_preprocessor_gui.py")

    # Find the line
    for i, line in enumerate(content.split('\n'), 1):
        if 'Pre-clean Input' in line:
            print(f"   Found at line {i}: {line.strip()}")
else:
    print("❌ Pre-clean button code NOT found in tts_preprocessor_gui.py")

# Check for preclean_input method
if 'def preclean_input' in content:
    print("✅ preclean_input() method IS present")
else:
    print("❌ preclean_input() method NOT found")

# Check for TextPreprocessor class
if 'class TextPreprocessor' in content:
    print("✅ TextPreprocessor class IS present")
else:
    print("❌ TextPreprocessor class NOT found")

print("\n" + "="*70)
print("GUI File Structure:")
print("="*70)

# Show class structure
classes = re.findall(r'^class (\w+)', content, re.MULTILINE)
print(f"Classes found: {', '.join(classes)}")

# Show button definitions
buttons = re.findall(r'self\.(\w+_btn)\s*=\s*ttk\.Button.*?text=["\']([^"\']+)', content)
print(f"\nButtons found ({len(buttons)}):")
for btn_name, btn_text in buttons:
    print(f"  - {btn_name}: '{btn_text}'")

print("\n" + "="*70)
print("If you don't see 'preclean_btn: 🔧 Pre-clean Input' above,")
print("your file may be out of date. Try:")
print("  git pull origin claude/refactor-code-011CUqxi1wVLw1FnCXvgN1JG")
print("="*70)
