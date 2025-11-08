#!/usr/bin/env python3
"""Test comprehensive TTS preprocessing with all new features"""

import sys
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent))

# Import with minimal dependencies
import re
import ftfy
import spacy

class TextPreprocessor:
    """Complete copy of preprocessing logic for testing"""
    _nlp = None

    @classmethod
    def _get_nlp(cls):
        if cls._nlp is None:
            cls._nlp = spacy.load("en_core_web_sm")
        return cls._nlp

    @staticmethod
    def clean_unicode(text):
        text = ftfy.fix_text(text)
        text = text.replace('·', "'")
        text = text.replace('■', '')
        text = text.replace('●', '')
        text = text.replace('∙', '')
        text = text.replace('•', '')
        return text

    @staticmethod
    def normalize_punctuation(text):
        text = re.sub(r'\?{2,}', '?', text)
        text = re.sub(r'!{2,}', '!', text)
        text = re.sub(r'\.{4,}', '…', text)
        text = re.sub(r'---', '—', text)
        text = re.sub(r'--', '—', text)
        text = re.sub(r' - ', ' — ', text)
        text = re.sub(r'\.\.\.', '…', text)
        text = re.sub(r'\.\s\.\s\.', '…', text)
        return text

    @staticmethod
    def normalize_symbols(text):
        text = text.replace('™', ' trademark')
        text = text.replace('®', ' registered')
        text = text.replace('©', ' copyright')
        text = text.replace(' & ', ' and ')
        text = text.replace('&', ' and ')
        text = re.sub(r'\s@\s', ' at ', text)
        text = re.sub(r'#(\d+)', r'number \1', text)
        return text

    @staticmethod
    def normalize_numbers(text):
        ordinals = {
            '1st': 'first', '2nd': 'second', '3rd': 'third', '4th': 'fourth',
            '5th': 'fifth', '6th': 'sixth', '7th': 'seventh', '8th': 'eighth',
            '9th': 'ninth', '10th': 'tenth', '11th': 'eleventh', '12th': 'twelfth',
            '13th': 'thirteenth', '14th': 'fourteenth', '15th': 'fifteenth',
            '16th': 'sixteenth', '17th': 'seventeenth', '18th': 'eighteenth',
            '19th': 'nineteenth', '20th': 'twentieth', '21st': 'twenty-first',
            '22nd': 'twenty-second', '23rd': 'twenty-third', '30th': 'thirtieth',
            '31st': 'thirty-first'
        }
        for ordinal, word in ordinals.items():
            text = re.sub(r'\b' + ordinal + r'\b', word, text, flags=re.IGNORECASE)
        text = re.sub(r'\b(\d{4})s\b', r'\1s', text)
        text = re.sub(r"\b'(\d{2})s\b", r'\1s', text)
        return text

    @staticmethod
    def normalize_currency(text):
        text = re.sub(r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)', r'\1 dollars', text)
        text = re.sub(r'€(\d+(?:,\d{3})*(?:\.\d{2})?)', r'\1 euros', text)
        text = re.sub(r'£(\d+(?:,\d{3})*(?:\.\d{2})?)', r'\1 pounds', text)
        text = re.sub(r'¢', ' cents', text)
        return text

    @staticmethod
    def normalize_all_caps(text):
        def convert_sentence(match):
            sentence = match.group(0)
            caps_count = sum(1 for c in sentence if c.isupper())
            total_alpha = sum(1 for c in sentence if c.isalpha())
            if total_alpha > 0 and (caps_count / total_alpha) > 0.7:
                words = sentence.split()
                converted = []
                for word in words:
                    word_caps_only = ''.join(c for c in word if c.isalpha())
                    if word_caps_only and word_caps_only.isupper():
                        if len(word_caps_only) <= 4:
                            converted.append(word)
                        else:
                            converted.append(word.capitalize())
                    else:
                        converted.append(word)
                return ' '.join(converted)
            return sentence
        text = re.sub(r'[^.!?]+[.!?]', convert_sentence, text)
        def convert_caps(match):
            word = match.group(0)
            if len(word) <= 4:
                return word
            return word.title()
        text = re.sub(r'\b[A-Z]{5,}\b', convert_caps, text)
        return text

    @staticmethod
    def normalize_chapter_markers(text):
        text = re.sub(r'\bCHAPTER\b', 'Chapter', text, flags=re.IGNORECASE)
        text = re.sub(r'\bPART\b', 'Part', text, flags=re.IGNORECASE)
        text = re.sub(r'\bSECTION\b', 'Section', text, flags=re.IGNORECASE)
        roman_map = {
            'I': '1', 'II': '2', 'III': '3', 'IV': '4', 'V': '5',
            'VI': '6', 'VII': '7', 'VIII': '8', 'IX': '9', 'X': '10',
        }
        for roman, arabic in roman_map.items():
            text = re.sub(r'\b(Chapter|Part|Section)\s+' + roman + r'\b',
                         r'\1 ' + arabic, text)
        return text

    @staticmethod
    def remove_urls_emails(text):
        text = re.sub(r'https?://[^\s]+', '[link]', text)
        text = re.sub(r'www\.[^\s]+', '[link]', text)
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[email]', text)
        text = re.sub(r' {2,}', ' ', text)
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


def test_comprehensive():
    """Test all preprocessing features"""

    test_file = Path("TEST_COMPREHENSIVE.txt")
    if not test_file.exists():
        print(f"Error: {test_file} not found!")
        return

    print("="*90)
    print(" "*20 + "COMPREHENSIVE TTS PREPROCESSING TEST")
    print("="*90)
    print()

    with open(test_file, 'r', encoding='utf-8') as f:
        original_text = f.read()

    print(f"📖 Original text:")
    print(f"   Size: {len(original_text):,} chars")
    print(f"   Lines: {original_text.count(chr(10)) + 1}")
    print()

    steps = [
        ("1. Clean Unicode", TextPreprocessor.clean_unicode),
        ("2. Normalize Punctuation", TextPreprocessor.normalize_punctuation),
        ("3. Normalize Symbols", TextPreprocessor.normalize_symbols),
        ("4. Normalize Numbers", TextPreprocessor.normalize_numbers),
        ("5. Normalize Currency", TextPreprocessor.normalize_currency),
        ("6. Normalize ALL CAPS", TextPreprocessor.normalize_all_caps),
        ("7. Normalize Chapters", TextPreprocessor.normalize_chapter_markers),
        ("8. Remove URLs/Emails", TextPreprocessor.remove_urls_emails),
        ("9. Remove Page Numbers", TextPreprocessor.remove_page_numbers),
        ("10. Fix Hyphenated Breaks", TextPreprocessor.fix_hyphenated_breaks),
        ("11. Normalize Whitespace", TextPreprocessor.normalize_whitespace),
        ("12. Chunk for TTS", lambda t: TextPreprocessor.chunk_for_tts(t, 250)),
    ]

    current_text = original_text

    for step_name, step_func in steps:
        before_size = len(current_text)
        current_text = step_func(current_text)
        after_size = len(current_text)
        change = after_size - before_size
        change_pct = (change / before_size * 100) if before_size > 0 else 0

        print(f"✓ {step_name}")
        print(f"   Before: {before_size:,} chars → After: {after_size:,} chars")
        print(f"   Change: {change:+,} chars ({change_pct:+.2f}%)")
        print()

    print("="*90)
    print("FINAL RESULT:")
    print("="*90)
    print(current_text)
    print()
    print("="*90)

    output_file = Path("TEST_COMPREHENSIVE_OUTPUT.txt")
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
    test_comprehensive()
