#!/usr/bin/env python3
"""Test the new TextPreprocessor without GUI dependencies"""

import re
from pathlib import Path
import ftfy
import spacy

# Minimal TextPreprocessor copy for testing
class TextPreprocessor:
    _nlp = None

    @classmethod
    def _get_nlp(cls):
        if cls._nlp is None:
            cls._nlp = spacy.load("en_core_web_sm")
        return cls._nlp

    @staticmethod
    def clean_unicode(text):
        # Fix encoding issues
        text = ftfy.fix_text(text)
        # Replace OCR artifacts
        text = text.replace('·', "'")
        text = text.replace('■', '')
        text = text.replace('●', '')
        text = text.replace('∙', '')
        text = text.replace('•', '')
        return text

    @staticmethod
    def remove_page_numbers(text):
        text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text

    @staticmethod
    def fix_hyphenated_breaks(text):
        text = re.sub(r'(\w+)-\s*\n\s*(\w+)', lambda m: m.group(1) + m.group(2), text)
        return text

    @staticmethod
    def normalize_whitespace(text):
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        text = re.sub(r' {2,}', ' ', text)
        text = re.sub(r' +$', '', text, flags=re.MULTILINE)
        text = re.sub(r'^ +', '', text, flags=re.MULTILINE)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text

    @staticmethod
    def segment_sentences(text):
        nlp = TextPreprocessor._get_nlp()
        doc = nlp(text)
        return [sent.text.strip() for sent in doc.sents if sent.text.strip()]

    @staticmethod
    def chunk_for_tts(text, max_chars=250):
        paragraphs = text.split('\n\n')
        all_chunks = []

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            sentences = TextPreprocessor.segment_sentences(paragraph)
            para_chunks = []
            current_chunk = ""

            for sentence in sentences:
                test_chunk = (current_chunk + " " + sentence).strip() if current_chunk else sentence

                if len(test_chunk) <= max_chars:
                    current_chunk = test_chunk
                else:
                    if current_chunk:
                        para_chunks.append(current_chunk)

                    if len(sentence) > max_chars:
                        comma_chunks = TextPreprocessor._split_at_commas(sentence, max_chars)
                        para_chunks.extend(comma_chunks)
                        current_chunk = ""
                    else:
                        current_chunk = sentence

            if current_chunk:
                para_chunks.append(current_chunk)

            all_chunks.extend(para_chunks)
            all_chunks.append("")

        while all_chunks and not all_chunks[-1]:
            all_chunks.pop()

        return '\n'.join(all_chunks)

    @staticmethod
    def _split_at_commas(sentence, max_chars):
        if ',' not in sentence:
            return TextPreprocessor._split_at_spaces(sentence, max_chars)

        parts = sentence.split(',')
        chunks = []
        current_chunk = ""

        for part in parts:
            part = part.strip()
            if not part:
                continue

            test_chunk = (current_chunk + ", " + part) if current_chunk else part

            if len(test_chunk) <= max_chars:
                current_chunk = test_chunk
            else:
                if current_chunk:
                    chunks.append(current_chunk)

                if len(part) > max_chars:
                    chunks.extend(TextPreprocessor._split_at_spaces(part, max_chars))
                    current_chunk = ""
                else:
                    current_chunk = part

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    @staticmethod
    def _split_at_spaces(text, max_chars):
        chunks = []
        words = text.split()
        current_chunk = ""

        for word in words:
            test_chunk = (current_chunk + " " + word).strip() if current_chunk else word

            if len(test_chunk) <= max_chars:
                current_chunk = test_chunk
            else:
                if current_chunk:
                    chunks.append(current_chunk)

                if len(word) > max_chars:
                    for i in range(0, len(word), max_chars):
                        chunks.append(word[i:i+max_chars])
                    current_chunk = ""
                else:
                    current_chunk = word

        if current_chunk:
            chunks.append(current_chunk)

        return chunks


def test_preprocessing():
    """Test the preprocessing pipeline"""

    test_file = Path("TEST_INPUT.txt")
    if not test_file.exists():
        print(f"Error: {test_file} not found!")
        return

    print("="*80)
    print("TESTING NEW TEXT PREPROCESSOR WITH spaCy + ftfy")
    print("="*80)
    print()

    with open(test_file, 'r', encoding='utf-8') as f:
        original_text = f.read()

    print(f"📖 Original text:")
    print(f"   Size: {len(original_text):,} chars")
    print(f"   Lines: {original_text.count(chr(10)) + 1}")
    print()

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

    print("="*80)
    print("FINAL RESULT:")
    print("="*80)
    print(current_text)
    print()
    print("="*80)

    output_file = Path("TEST_OUTPUT.txt")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(current_text)

    print(f"✓ Saved to: {output_file}")
    print(f"   Original: {len(original_text):,} chars")
    print(f"   Final:    {len(current_text):,} chars")
    print(f"   Change:   {len(current_text) - len(original_text):+,} chars")

    data_loss_pct = ((len(original_text) - len(current_text)) / len(original_text)) * 100
    if data_loss_pct > 5:
        print(f"⚠️  WARNING: Data loss {data_loss_pct:.1f}%!")
    else:
        print(f"✓ Data integrity OK (loss: {data_loss_pct:.2f}%)")

if __name__ == "__main__":
    test_preprocessing()
