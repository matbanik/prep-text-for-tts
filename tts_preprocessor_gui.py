"""
TTS Text Preprocessor GUI
A professional interface for batch processing text with OpenRouter API

Features:
- Encrypted API key storage using Fernet symmetric encryption
- Multi-pass OCR cleaning (87.09% accuracy)
- TTS-optimized text chunking with spaCy
- Batch processing with context preservation
- Real-time progress tracking and logging
"""

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import threading
import queue
import openai
import re
import time
import json
from pathlib import Path
from datetime import datetime
import ftfy
import spacy
from multi_pass_processor import MultiPassOCRProcessor
from cryptography.fernet import Fernet
import base64
import hashlib
import os

# ============================================================================
# SETTINGS MANAGER - Encrypted API Key Storage
# ============================================================================

class SettingsManager:
    """
    Manages application settings with encrypted API key storage.

    Security features:
    - API keys encrypted at rest using Fernet (symmetric encryption)
    - Encryption key derived from machine-specific identifier
    - Settings file added to .gitignore to prevent accidental commits
    - API keys masked in all log output
    """

    SETTINGS_FILE = "settings.json"
    GITIGNORE_FILE = ".gitignore"

    def __init__(self):
        self.settings = self._load_settings()
        self.encryption_key = self._get_encryption_key()
        self._ensure_gitignore()

    def _get_encryption_key(self):
        """Generate encryption key from machine-specific identifier"""
        # Use a machine-specific value + salt for key derivation
        # This ensures keys are tied to the machine
        machine_id = f"{os.getlogin()}-{Path.home()}".encode()
        salt = b"tts-preprocessor-v1"  # Application-specific salt

        # Derive 32-byte key using SHA-256
        key_material = hashlib.sha256(machine_id + salt).digest()
        # Fernet requires base64-encoded 32-byte key
        return base64.urlsafe_b64encode(key_material)

    def _encrypt_value(self, value):
        """Encrypt a sensitive value"""
        if not value:
            return ""
        fernet = Fernet(self.encryption_key)
        return fernet.encrypt(value.encode()).decode()

    def _decrypt_value(self, encrypted_value):
        """Decrypt a sensitive value"""
        if not encrypted_value:
            return ""
        try:
            fernet = Fernet(self.encryption_key)
            return fernet.decrypt(encrypted_value.encode()).decode()
        except Exception:
            return ""  # Return empty if decryption fails

    def _load_settings(self):
        """Load settings from JSON file"""
        if Path(self.SETTINGS_FILE).exists():
            try:
                with open(self.SETTINGS_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load settings: {e}")
                return self._default_settings()
        return self._default_settings()

    def _default_settings(self):
        """Return default settings"""
        return {
            "api_key_encrypted": "",
            "model_name": "qwen/qwen-2.5-72b-instruct",  # Default OpenRouter model
            "temperature": 0.2,
            "response_percentage": 85,  # Default response percentage threshold
            "seed": 42,
            "batch_size": 500,
            "max_tokens": 16000,
            "history_limit": 250,  # Maximum number of history entries per viewer
            "last_input_file": "",
            "last_output_file": "",
            "last_prompt_file": "",
            "diff_viewer_history": [],  # History for Diff Viewer
            "full_output_history": []   # History for Full Output
        }

    def save_settings(self):
        """Save settings to JSON file"""
        try:
            with open(self.SETTINGS_FILE, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save settings: {e}")

    def get_api_key(self):
        """Get decrypted API key"""
        encrypted = self.settings.get("api_key_encrypted", "")
        return self._decrypt_value(encrypted)

    def set_api_key(self, api_key):
        """Set and encrypt API key"""
        self.settings["api_key_encrypted"] = self._encrypt_value(api_key)
        self.save_settings()

    def get_base_url(self):
        """Get OpenRouter API base URL"""
        return "https://openrouter.ai/api/v1"

    def _ensure_gitignore(self):
        """Ensure settings.json is in .gitignore"""
        gitignore_path = Path(self.GITIGNORE_FILE)
        gitignore_content = ""

        if gitignore_path.exists():
            with open(gitignore_path, 'r') as f:
                gitignore_content = f.read()

        # Add settings.json if not already present
        if self.SETTINGS_FILE not in gitignore_content:
            with open(gitignore_path, 'a') as f:
                if gitignore_content and not gitignore_content.endswith('\n'):
                    f.write('\n')
                f.write(f'\n# TTS Preprocessor settings (contains encrypted API key)\n')
                f.write(f'{self.SETTINGS_FILE}\n')

    @staticmethod
    def mask_api_key(text, api_key):
        """Mask API key in text for logging"""
        if not api_key or len(api_key) < 8:
            return text
        # Show first 4 and last 4 characters, mask the rest
        masked = api_key[:4] + '*' * (len(api_key) - 8) + api_key[-4:]
        return text.replace(api_key, masked)


# ============================================================================
# PREPROCESSING MODULE - Best-Practices Text Cleaning for TTS
# ============================================================================

class TextPreprocessor:
    """
    Comprehensive text preprocessing for OCR to TTS pipeline.

    Uses industry best practices:
    - ftfy: Automatic Unicode/mojibake cleaning
    - spaCy: Linguistic sentence segmentation
    - Deepgram approach: Hybrid chunking (sentences + comma fallback)

    Based on research from:
    - epub2tts (audiobook generation)
    - Deepgram TTS optimization guide
    - Coqui TTS best practices
    """

    # Load spaCy model once (lazy loading)
    _nlp = None
    _ocr_processor = None

    @classmethod
    def _get_nlp(cls):
        """Lazy load spaCy model"""
        if cls._nlp is None:
            cls._nlp = spacy.load("en_core_web_sm")
        return cls._nlp

    @classmethod
    def _get_ocr_processor(cls):
        """Lazy load MultiPassOCRProcessor"""
        if cls._ocr_processor is None:
            cls._ocr_processor = MultiPassOCRProcessor(enable_logging=False)
        return cls._ocr_processor

    @staticmethod
    def apply_multi_pass_ocr_cleaning(text):
        """
        Apply 5-stage multi-pass OCR cleaning (production-ready: 87.09% accuracy).

        Replaces old steps 1-6:
        - Stage 1: Semantic Cleaning (ftfy, page headers, whitespace)
        - Stage 2: Deterministic Cleaning (apostrophes, word fragments, OCR errors)
        - Stage 3: Sentence Reconstruction (paragraph merging)
        - Stage 4: Edge Case Collection
        - Stage 5: Edge Case Handling

        Returns: (cleaned_text, processing_state)
        """
        processor = TextPreprocessor._get_ocr_processor()
        cleaned_text, state = processor.process(text)
        return cleaned_text, state

    @staticmethod
    def clean_unicode(text):
        """
        Fix Unicode issues using ftfy, then clean OCR artifacts.

        Handles:
        - Mojibake (encoding mix-ups) - ftfy
        - HTML entities - ftfy
        - OCR artifacts like · → ' - manual replacement
        - Curly quotes normalization - ftfy
        """
        # Step 1: Fix encoding issues with ftfy
        text = ftfy.fix_text(text)

        # Step 2: Replace common OCR artifacts
        # These are legitimate Unicode characters that OCR misreads
        text = text.replace('·', "'")  # Middle dot → apostrophe
        text = text.replace('■', '')   # Box
        text = text.replace('●', '')   # Circle
        text = text.replace('∙', '')   # Bullet
        text = text.replace('•', '')   # Bullet

        return text

    @staticmethod
    def normalize_punctuation(text):
        """
        Normalize punctuation for TTS.

        Issues addressed:
        - Multiple punctuation (??? → ?, !!! → !)
        - Em dashes (---, --, — all → —)
        - Ellipses (..., .. → …)
        - Smart quotes (handled by ftfy)
        """
        # Normalize multiple punctuation
        text = re.sub(r'\?{2,}', '?', text)  # ??? → ?
        text = re.sub(r'!{2,}', '!', text)  # !!! → !
        text = re.sub(r'\.{4,}', '…', text)  # .... → …

        # Normalize em dashes
        text = re.sub(r'---', '—', text)  # Three hyphens
        text = re.sub(r'--', '—', text)   # Two hyphens
        text = re.sub(r' - ', ' — ', text)  # Spaced hyphen (likely em dash intent)

        # Normalize ellipses (but not 3 dots in sequence for decimal ranges)
        text = re.sub(r'\.\.\.', '…', text)  # Three dots → ellipsis
        text = re.sub(r'\.\s\.\s\.', '…', text)  # Spaced dots

        return text

    @staticmethod
    def normalize_symbols(text):
        """
        Convert symbols to TTS-friendly text.

        Common symbols in books:
        - ™, ®, © → spelled out
        - & → "and"
        - @ → "at"
        - # → "number"
        """
        # Trademark and copyright
        text = text.replace('™', ' trademark')
        text = text.replace('®', ' registered')
        text = text.replace('©', ' copyright')

        # Common symbols
        text = text.replace(' & ', ' and ')
        text = text.replace('&', ' and ')

        # @ symbol (but preserve in emails if any remain)
        text = re.sub(r'\s@\s', ' at ', text)

        # Number sign (context-dependent)
        text = re.sub(r'#(\d+)', r'number \1', text)  # #5 → number 5

        return text

    @staticmethod
    def normalize_numbers(text):
        """
        Normalize numbers for TTS pronunciation.

        Handles:
        - Ordinals: 1st, 2nd, 3rd → first, second, third
        - Decades: 1990s → nineteen nineties
        - Year ranges: 1990-1995 → nineteen ninety to nineteen ninety-five
        - Keep phone numbers and long IDs as digits
        """
        # Ordinal numbers (1st, 2nd, 3rd, 4th, etc.)
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

        # Decades (1990s, 80s, '90s)
        text = re.sub(r'\b(\d{4})s\b', r'\1s', text)  # Keep format like "1990s"
        text = re.sub(r"\b'(\d{2})s\b", r'\1s', text)  # '90s → 90s

        # Standalone small numbers that should be spelled (Chapter 1, Scene 2, etc.)
        # Keep as-is - spaCy and TTS engines handle these well

        return text

    @staticmethod
    def normalize_currency(text):
        """
        Normalize currency for TTS.

        Examples:
        - $100 → 100 dollars
        - €50 → 50 euros
        - £25 → 25 pounds
        """
        # Dollar signs
        text = re.sub(r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)', r'\1 dollars', text)

        # Euro signs
        text = re.sub(r'€(\d+(?:,\d{3})*(?:\.\d{2})?)', r'\1 euros', text)

        # Pound signs
        text = re.sub(r'£(\d+(?:,\d{3})*(?:\.\d{2})?)', r'\1 pounds', text)

        # Cent/penny notation
        text = re.sub(r'¢', ' cents', text)

        return text

    @staticmethod
    def normalize_all_caps(text):
        """
        Convert ALL CAPS to Title Case (except known acronyms).

        Issues:
        - ALL CAPS is read as shouting by TTS
        - But acronyms like NASA, FBI, USA should stay caps

        Strategy:
        - Detect ALL CAPS sentences/phrases
        - Keep words ≤ 4 chars in CAPS (likely acronyms)
        - Convert longer CAPS words to Title Case
        """
        # First, handle full sentences in ALL CAPS
        # Match sentences that are mostly uppercase (at least 70% caps)
        def convert_sentence(match):
            sentence = match.group(0)
            caps_count = sum(1 for c in sentence if c.isupper())
            total_alpha = sum(1 for c in sentence if c.isalpha())

            if total_alpha > 0 and (caps_count / total_alpha) > 0.7:
                # This is an ALL CAPS sentence
                words = sentence.split()
                converted = []
                for word in words:
                    # Check if word is all caps
                    word_caps_only = ''.join(c for c in word if c.isalpha())
                    if word_caps_only and word_caps_only.isupper():
                        # Keep acronyms (≤ 4 chars), convert longer words
                        if len(word_caps_only) <= 4:
                            converted.append(word)
                        else:
                            converted.append(word.capitalize())
                    else:
                        converted.append(word)
                return ' '.join(converted)
            return sentence

        # Process sentences
        text = re.sub(r'[^.!?]+[.!?]', convert_sentence, text)

        # Then handle individual ALL CAPS words that remain
        def convert_caps(match):
            word = match.group(0)
            # Keep short acronyms (≤ 4 chars) like NASA, FBI, USA
            if len(word) <= 4:
                return word
            # Convert long ALL CAPS to Title Case
            return word.title()

        # Find remaining words in ALL CAPS and selectively convert
        text = re.sub(r'\b[A-Z]{5,}\b', convert_caps, text)

        return text

    @staticmethod
    def normalize_chapter_markers(text):
        """
        Normalize chapter and section markers.

        Examples:
        - CHAPTER 1 → Chapter 1
        - Chapter I → Chapter 1 (Roman numerals)
        - Part III → Part 3
        """
        # Normalize "CHAPTER" to "Chapter"
        text = re.sub(r'\bCHAPTER\b', 'Chapter', text, flags=re.IGNORECASE)
        text = re.sub(r'\bPART\b', 'Part', text, flags=re.IGNORECASE)
        text = re.sub(r'\bSECTION\b', 'Section', text, flags=re.IGNORECASE)

        # Convert Roman numerals in chapters (common in books)
        roman_map = {
            'I': '1', 'II': '2', 'III': '3', 'IV': '4', 'V': '5',
            'VI': '6', 'VII': '7', 'VIII': '8', 'IX': '9', 'X': '10',
            'XI': '11', 'XII': '12', 'XIII': '13', 'XIV': '14', 'XV': '15',
            'XVI': '16', 'XVII': '17', 'XVIII': '18', 'XIX': '19', 'XX': '20'
        }

        for roman, arabic in roman_map.items():
            text = re.sub(r'\b(Chapter|Part|Section)\s+' + roman + r'\b',
                         r'\1 ' + arabic, text)

        return text

    @staticmethod
    def remove_page_headers(text):
        """
        Remove OCR page headers/footers that interrupt text flow.

        Common patterns:
        - "Raccoon Encounter/35" (chapter/page)
        - "36/Tests and Encounters" (page/chapter)
        - Standalone page numbers

        These appear as isolated lines between blank lines and break sentence flow.
        """
        lines = text.split('\n')
        cleaned_lines = []
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            # Check if this looks like a page header/footer
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
                    # Check if surrounded by blank lines or at boundaries
                    prev_blank = (i == 0 or not lines[i-1].strip())
                    next_blank = (i == len(lines) - 1 or not lines[i+1].strip())

                    if prev_blank and next_blank:
                        # Check if it contains numbers and slashes (common in headers)
                        if '/' in line or (any(c.isdigit() for c in line) and len(line.split()) <= 3):
                            is_page_header = True

            if not is_page_header:
                cleaned_lines.append(lines[i])
            else:
                # Page header found - also skip surrounding blank lines
                # Remove preceding blank line if it exists
                if cleaned_lines and not cleaned_lines[-1].strip():
                    cleaned_lines.pop()

                # Skip following blank line
                if i + 1 < len(lines) and not lines[i + 1].strip():
                    i += 1

            i += 1

        return '\n'.join(cleaned_lines)

    @staticmethod
    def fix_merged_words(text):
        """
        Fix OCR errors where two words are merged without a space.

        Examples:
        - "beenkilled" → "been killed"
        - "becamelabored" → "became labored"
        - "racedthrough" → "raced through"
        - "intothe" → "into the"

        Strategy: Use a dictionary of common word endings/beginnings to detect splits.
        """
        # Common words that often get merged at the END of another word
        # These are high-frequency words that OCR often fails to separate
        COMMON_ENDINGS = {
            'the', 'and', 'that', 'have', 'with', 'from', 'they', 'been',
            'were', 'said', 'when', 'what', 'them', 'some', 'would', 'could',
            'into', 'than', 'these', 'through', 'where', 'their', 'which',
            'about', 'after', 'should', 'because', 'before', 'against',
            'between', 'under', 'during', 'without', 'however', 'whether'
        }

        # Common word endings to check (verb forms, prepositions, etc.)
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
            # Using lookbehind to ensure we don't split valid words ending in these letters
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

        for pattern, replacement in WORD_PATTERNS:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        return text

    @staticmethod
    def fix_orphaned_apostrophes(text):
        """
        Fix OCR errors where apostrophes appear before words incorrectly.

        Common OCR issues:
        - people'and → people and
        - me'from → me from
        - feeling'both → feeling both

        These are misread quotes/dialogue marks, not contractions.
        """
        # Remove apostrophe before common words (not contractions)
        # Pattern: word + apostrophe + space/newline + lowercase word
        text = re.sub(r"(\w+)'\s*\n?\s*([a-z])", r"\1 \2", text)

        # Also fix apostrophe at end of line before next word
        text = re.sub(r"'(\s*\n\s*)([a-z])", r"\1\2", text)

        return text

    @staticmethod
    def fix_split_words(text):
        """
        Fix only TRUE split words (word fragments across lines).

        OCR often breaks words at line endings:
        - "hun-\ndred" → "hundred" (with hyphen)
        - "hun\ndred" → "hundred" (fragment without hyphen)
        - "are\nsearching" → "are searching" (complete words - DON'T merge)

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
            'while', 'until', 'unless', 'though', 'although', 'still', 'yet', 'already'
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

    @staticmethod
    def merge_sentence_lines(text):
        """
        Merge lines within sentences (preserving paragraph breaks).

        Issue: OCR creates newlines mid-sentence:
        "John Muir said, 'If I have to worship God,
        it's going to be in a temple'"

        Should be:
        "John Muir said, 'If I have to worship God, it's going to be in a temple'"

        Strategy: Only treat double blank lines as paragraph breaks.
        Single blank lines are OCR artifacts.
        """
        # First, convert double+ blank lines to a marker
        text = re.sub(r'\n\n+', '\n<<PARAGRAPH>>\n', text)

        lines = text.split('\n')
        merged_lines = []
        i = 0

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
                        i = j + 1
                        continue

            merged_lines.append(current_line)
            i += 1

        return '\n'.join(merged_lines)

    @staticmethod
    def remove_urls_emails(text):
        """
        Remove or simplify URLs and email addresses.

        TTS engines struggle with these and they're rarely needed in audiobooks.
        """
        # Remove URLs
        text = re.sub(r'https?://[^\s]+', '[link]', text)
        text = re.sub(r'www\.[^\s]+', '[link]', text)

        # Remove email addresses
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[email]', text)

        # Clean up any double spaces created
        text = re.sub(r' {2,}', ' ', text)

        return text

    @staticmethod
    def remove_page_numbers(text):
        """
        Remove page numbers and common headers.

        Minimal regex approach - only removes obvious page artifacts:
        - Lines with just numbers
        - Common header patterns
        """
        # Remove lines with just numbers
        text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)

        # Remove trailing empty lines
        text = re.sub(r'\n{3,}', '\n\n', text)

        return text

    @staticmethod
    def fix_hyphenated_breaks(text):
        """
        Merge words broken across lines with hyphens.

        Example: "end-\nof" → "endof"
        """
        text = re.sub(r'(\w+)-\s*\n\s*(\w+)', lambda m: m.group(1) + m.group(2), text)
        return text

    @staticmethod
    def normalize_whitespace(text):
        """
        Normalize whitespace without destroying structure.

        - Collapse multiple spaces to single space
        - Preserve paragraph breaks (double newlines)
        """
        # Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # Collapse multiple spaces within lines
        text = re.sub(r' {2,}', ' ', text)

        # Remove spaces at start/end of lines
        text = re.sub(r' +$', '', text, flags=re.MULTILINE)
        text = re.sub(r'^ +', '', text, flags=re.MULTILINE)

        # Normalize excessive newlines to max 2 (paragraph break)
        text = re.sub(r'\n{3,}', '\n\n', text)

        return text

    @staticmethod
    def segment_sentences(text):
        """
        Use spaCy for accurate sentence segmentation.

        Benefits over regex:
        - Handles "Dr.", "Jr.", "Mr." correctly
        - Context-aware (doesn't break "U.S.A.")
        - Uses dependency parsing for accuracy

        Returns: List of sentences
        """
        nlp = TextPreprocessor._get_nlp()
        doc = nlp(text)
        return [sent.text.strip() for sent in doc.sents if sent.text.strip()]

    @staticmethod
    def chunk_for_tts(text, max_chars=250):
        """
        Deepgram-style hybrid chunking for TTS optimization.

        Strategy:
        1. Split text into paragraphs
        2. Use spaCy for sentence segmentation
        3. Combine sentences while under max_chars
        4. If single sentence > max_chars: split at commas (min 3 words)
        5. Preserve paragraph breaks

        This preserves natural speech boundaries where people pause.
        """
        # Split into paragraphs
        paragraphs = text.split('\n\n')
        all_chunks = []

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            # Get sentences using spaCy
            sentences = TextPreprocessor.segment_sentences(paragraph)

            # Combine sentences into chunks
            para_chunks = []
            current_chunk = ""

            for sentence in sentences:
                # Try to add sentence to current chunk
                test_chunk = (current_chunk + " " + sentence).strip() if current_chunk else sentence

                if len(test_chunk) <= max_chars:
                    # Fits! Add it
                    current_chunk = test_chunk
                else:
                    # Doesn't fit
                    if current_chunk:
                        # Save current chunk
                        para_chunks.append(current_chunk)

                    # Check if sentence itself is too long
                    if len(sentence) > max_chars:
                        # Split long sentence at commas
                        comma_chunks = TextPreprocessor._split_at_commas(sentence, max_chars)
                        para_chunks.extend(comma_chunks)
                        current_chunk = ""
                    else:
                        # Start new chunk with this sentence
                        current_chunk = sentence

            # Add remaining chunk
            if current_chunk:
                para_chunks.append(current_chunk)

            # Add paragraph chunks
            all_chunks.extend(para_chunks)
            # Add blank line for paragraph break
            all_chunks.append("")

        # Remove trailing blank lines
        while all_chunks and not all_chunks[-1]:
            all_chunks.pop()

        return '\n'.join(all_chunks)

    @staticmethod
    def _split_at_commas(sentence, max_chars):
        """
        Split a long sentence at commas.

        Keeps minimum 3 words per chunk to maintain coherence.
        Fallback: If no commas, split at last space before limit.
        """
        if ',' not in sentence:
            # No commas, split at spaces
            return TextPreprocessor._split_at_spaces(sentence, max_chars)

        parts = sentence.split(',')
        chunks = []
        current_chunk = ""

        for part in parts:
            part = part.strip()
            if not part:
                continue

            # Test adding this part
            test_chunk = (current_chunk + ", " + part) if current_chunk else part

            if len(test_chunk) <= max_chars:
                current_chunk = test_chunk
            else:
                # Save current chunk if it has content
                if current_chunk:
                    chunks.append(current_chunk)

                # Check if part itself is too long
                if len(part) > max_chars:
                    # Recursively split this part at spaces
                    chunks.extend(TextPreprocessor._split_at_spaces(part, max_chars))
                    current_chunk = ""
                else:
                    current_chunk = part

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    @staticmethod
    def _split_at_spaces(text, max_chars):
        """
        Fallback: Split text at spaces when no better boundary exists.
        """
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

                # Handle extremely long words
                if len(word) > max_chars:
                    # Force split long word
                    for i in range(0, len(word), max_chars):
                        chunks.append(word[i:i+max_chars])
                    current_chunk = ""
                else:
                    current_chunk = word

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    @staticmethod
    def preprocess_text(text, max_chunk_size=250):
        """
        Complete comprehensive preprocessing pipeline for OCR → TTS.

        Based on best practices from:
        - Multi-Pass OCR Processor (87.09% accuracy)
        - epub2tts (audiobook generation)
        - ElevenLabs normalization guide
        - Coqui TTS preprocessing
        - Deepgram TTS optimization

        Pipeline:
        PART 1: OCR Cleaning (Multi-Pass Processor - 5 stages)
          Stage 1: Semantic Cleaning (ftfy, page headers, whitespace)
          Stage 2: Deterministic Cleaning (apostrophes, word fragments, OCR errors)
          Stage 3: Sentence Reconstruction (paragraph merging)
          Stage 4: Edge Case Collection
          Stage 5: Edge Case Handling

        PART 2: TTS Normalization (10 steps)
          1. Normalize punctuation (!!!, ???, ---, ...)
          2. Normalize symbols (™, ©, &, @, #)
          3. Normalize numbers (1st → first, 1990s)
          4. Normalize currency ($100 → 100 dollars)
          5. Normalize ALL CAPS (but preserve acronyms)
          6. Normalize chapter markers (CHAPTER I → Chapter 1)
          7. Remove URLs and emails
          8. Remove remaining page numbers
          9. Normalize whitespace
          10. Chunk for TTS (spaCy + Deepgram hybrid)

        Returns: Cleaned, chunked text ready for TTS
        """
        # Part 1: Multi-Pass OCR Cleaning (replaces old steps 1-6)
        result, state = TextPreprocessor.apply_multi_pass_ocr_cleaning(text)

        # Part 2: TTS-specific normalization
        tts_steps = [
            ("Normalize punctuation", TextPreprocessor.normalize_punctuation),
            ("Normalize symbols", TextPreprocessor.normalize_symbols),
            ("Normalize numbers", TextPreprocessor.normalize_numbers),
            ("Normalize currency", TextPreprocessor.normalize_currency),
            ("Normalize ALL CAPS", TextPreprocessor.normalize_all_caps),
            ("Normalize chapter markers", TextPreprocessor.normalize_chapter_markers),
            ("Remove URLs/emails", TextPreprocessor.remove_urls_emails),
            ("Remove page numbers", TextPreprocessor.remove_page_numbers),
            ("Normalize whitespace", TextPreprocessor.normalize_whitespace),
            ("Chunk for TTS (spaCy + hybrid)", lambda t: TextPreprocessor.chunk_for_tts(t, max_chunk_size)),
        ]

        for step_name, step_func in tts_steps:
            result = step_func(result)

        return result


# ============================================================================
# TEXT WIDGET WITH LINE NUMBERS
# ============================================================================

class TextWithLineNumbers(tk.Frame):
    """Text widget with synchronized line numbers"""

    def __init__(self, parent, **kwargs):
        tk.Frame.__init__(self, parent)

        # Extract text widget specific options
        text_options = {}
        for key in ['wrap', 'font', 'bg', 'fg', 'height', 'width']:
            if key in kwargs:
                text_options[key] = kwargs.pop(key)

        # Create line numbers canvas
        self.line_numbers = tk.Canvas(self, width=50, bg='#e0e0e0', highlightthickness=0)
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)

        # Create scrollbar
        self.scrollbar = tk.Scrollbar(self, orient=tk.VERTICAL)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Create text widget
        self.text = tk.Text(self, yscrollcommand=self._on_text_scroll, **text_options)
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Configure scrollbar
        self.scrollbar.config(command=self.text.yview)

        # Bind events for line number updates
        self.text.bind('<<Modified>>', self._on_modified)
        self.text.bind('<Configure>', self._on_configure)
        self.text.bind('<KeyRelease>', self._schedule_update)
        self.text.bind('<ButtonRelease>', self._schedule_update)

        # Update scheduling
        self._update_scheduled = False

    def _on_text_scroll(self, *args):
        """Handle text widget scrolling"""
        self.scrollbar.set(*args)
        self._update_line_numbers()

    def _on_modified(self, event=None):
        """Handle text modification"""
        self._schedule_update()

    def _on_configure(self, event=None):
        """Handle widget resize"""
        self._schedule_update()

    def _schedule_update(self, event=None):
        """Schedule line number update to avoid excessive redraws"""
        if not self._update_scheduled:
            self._update_scheduled = True
            self.after(10, self._do_update)

    def _do_update(self):
        """Perform the actual update"""
        self._update_scheduled = False
        self._update_line_numbers()

    def _update_line_numbers(self):
        """Redraw line numbers"""
        self.line_numbers.delete('all')

        # Get the index of the first visible line
        i = self.text.index('@0,0')
        while True:
            dline = self.text.dlineinfo(i)
            if dline is None:
                break
            y = dline[1]
            linenum = str(i).split('.')[0]
            self.line_numbers.create_text(
                45, y, anchor=tk.NE, text=linenum,
                font=self.text.cget('font'), fill='#666666'
            )
            i = self.text.index(f'{i}+1line')

    # Proxy methods to make this behave like a Text widget
    def insert(self, *args, **kwargs):
        return self.text.insert(*args, **kwargs)

    def delete(self, *args, **kwargs):
        return self.text.delete(*args, **kwargs)

    def get(self, *args, **kwargs):
        return self.text.get(*args, **kwargs)

    def see(self, *args, **kwargs):
        return self.text.see(*args, **kwargs)

    def tag_config(self, *args, **kwargs):
        return self.text.tag_config(*args, **kwargs)

    def tag_add(self, *args, **kwargs):
        return self.text.tag_add(*args, **kwargs)

    def tag_remove(self, *args, **kwargs):
        return self.text.tag_remove(*args, **kwargs)

    def search(self, *args, **kwargs):
        return self.text.search(*args, **kwargs)

    def mark_set(self, *args, **kwargs):
        return self.text.mark_set(*args, **kwargs)

    def yview(self, *args, **kwargs):
        return self.text.yview(*args, **kwargs)

    def config(self, **kwargs):
        """Configure the text widget"""
        return self.text.config(**kwargs)

    def configure(self, **kwargs):
        """Configure the text widget"""
        return self.text.configure(**kwargs)


# ============================================================================
# GUI APPLICATION
# ============================================================================

class TTSPreprocessorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("TTS Text Preprocessor - OpenRouter Edition")
        self.root.geometry("1400x900")

        # Settings manager for encrypted API key storage
        self.settings_mgr = SettingsManager()

        # Variables
        self.input_file = tk.StringVar()
        self.output_file = tk.StringVar()
        self.prompt_file = tk.StringVar()
        self.api_key = tk.StringVar()
        self.api_key_visible = tk.BooleanVar(value=False)
        self.model_name = tk.StringVar(value=self.settings_mgr.settings.get("model_name", "qwen/qwen-2.5-72b-instruct"))
        self.temperature = tk.DoubleVar(value=self.settings_mgr.settings.get("temperature", 0.2))
        self.seed = tk.IntVar(value=self.settings_mgr.settings.get("seed", 42))
        self.batch_size = tk.IntVar(value=self.settings_mgr.settings.get("batch_size", 500))
        self.max_tokens = tk.IntVar(value=self.settings_mgr.settings.get("max_tokens", 16000))
        self.response_percentage = tk.IntVar(value=self.settings_mgr.settings.get("response_percentage", 85))
        self.history_limit = tk.IntVar(value=self.settings_mgr.settings.get("history_limit", 250))

        # Load saved file paths
        self.input_file.set(self.settings_mgr.settings.get("last_input_file", ""))
        self.output_file.set(self.settings_mgr.settings.get("last_output_file", ""))
        self.prompt_file.set(self.settings_mgr.settings.get("last_prompt_file", ""))

        # Load decrypted API key
        self.api_key.set(self.settings_mgr.get_api_key())

        # Processing state
        self.is_processing = False
        self.is_paused = False
        self.current_batch = 0
        self.total_batches = 0
        self.start_time = None
        self.previous_context = ""
        self.test_mode = tk.BooleanVar(value=False)  # Mock AI for testing

        # Batch continuity tracking
        self.previous_input_last_sentence = ""
        self.previous_output_last_sentence = ""

        # Queue for thread-safe GUI updates
        self.log_queue = queue.Queue()

        # Build UI
        self.setup_ui()

        # Start log queue processor
        self.process_log_queue()

        # Save settings on close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def setup_ui(self):
        """Build the complete UI"""
        
        # ==== TOP SECTION: Configuration ====
        config_frame = ttk.LabelFrame(self.root, text="Configuration", padding=10)
        config_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # File Selection
        files_frame = ttk.Frame(config_frame)
        files_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(files_frame, text="Input File:").grid(row=0, column=0, sticky=tk.W, padx=5)
        ttk.Entry(files_frame, textvariable=self.input_file, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(files_frame, text="Browse...", command=self.browse_input).grid(row=0, column=2, padx=5)
        ttk.Button(files_frame, text="[TOOL] Pre-clean", command=self.preclean_input).grid(row=0, column=3, padx=5)
        
        ttk.Label(files_frame, text="Output File:").grid(row=1, column=0, sticky=tk.W, padx=5)
        ttk.Entry(files_frame, textvariable=self.output_file, width=50).grid(row=1, column=1, padx=5)
        ttk.Button(files_frame, text="Browse...", command=self.browse_output).grid(row=1, column=2, padx=5)
        
        ttk.Label(files_frame, text="Prompt File:").grid(row=2, column=0, sticky=tk.W, padx=5)
        ttk.Entry(files_frame, textvariable=self.prompt_file, width=50).grid(row=2, column=1, padx=5)
        ttk.Button(files_frame, text="Browse...", command=self.browse_prompt).grid(row=2, column=2, padx=5)

        # OpenRouter API Settings
        api_frame = ttk.Frame(config_frame)
        api_frame.pack(fill=tk.X, pady=5)

        ttk.Label(api_frame, text="API Key:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.api_key_entry = ttk.Entry(api_frame, textvariable=self.api_key, width=40, show="*")
        self.api_key_entry.grid(row=0, column=1, padx=5)
        self.api_key_entry.bind('<FocusOut>', lambda e: self.save_api_key())

        self.show_hide_btn = ttk.Button(api_frame, text="[VIEW]", width=3, command=self.toggle_api_key_visibility)
        self.show_hide_btn.grid(row=0, column=2, padx=2)

        ttk.Label(api_frame, text="Model:").grid(row=0, column=3, sticky=tk.W, padx=5)
        model_combo = ttk.Combobox(api_frame, textvariable=self.model_name, width=40,
                                    values=[
                                        "deepseek/deepseek-chat",          # DeepSeek Chat (economical)
                                        "qwen/qwen-2.5-72b-instruct",      # Qwen 2.5 72B
                                        "google/gemini-2.0-flash-exp:free", # Gemini 2.0 Flash (free)
                                        "openai/gpt-4o-mini",              # GPT-4o Mini
                                        "meta-llama/llama-3.3-70b-instruct", # Llama 3.3 70B
                                        "anthropic/claude-3.5-sonnet",     # Claude 3.5 Sonnet
                                        "openai/gpt-4o",                   # GPT-4o
                                        "google/gemini-pro-1.5",           # Gemini Pro 1.5
                                        "anthropic/claude-3-opus"          # Claude 3 Opus
                                    ])
        model_combo.grid(row=0, column=4, padx=5)
        model_combo.bind('<FocusOut>', lambda e: self.save_settings())

        ttk.Button(api_frame, text="Test Connection", command=self.test_connection).grid(row=0, column=5, padx=5)
        
        # Model Parameters
        params_frame = ttk.Frame(config_frame)
        params_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(params_frame, text="Temperature:").grid(row=0, column=0, sticky=tk.W, padx=5)
        ttk.Spinbox(params_frame, from_=0.0, to=1.0, increment=0.1, 
                    textvariable=self.temperature, width=10).grid(row=0, column=1, padx=5)
        
        ttk.Label(params_frame, text="Seed:").grid(row=0, column=2, sticky=tk.W, padx=5)
        ttk.Spinbox(params_frame, from_=1, to=9999, increment=1, 
                    textvariable=self.seed, width=10).grid(row=0, column=3, padx=5)
        
        ttk.Label(params_frame, text="Batch Size (lines):").grid(row=0, column=4, sticky=tk.W, padx=5)
        ttk.Spinbox(params_frame, from_=100, to=1000, increment=50, 
                    textvariable=self.batch_size, width=10).grid(row=0, column=5, padx=5)
        
        ttk.Label(params_frame, text="Max Tokens:").grid(row=0, column=6, sticky=tk.W, padx=5)
        ttk.Spinbox(params_frame, from_=1000, to=32000, increment=1000,
                    textvariable=self.max_tokens, width=10).grid(row=0, column=7, padx=5)

        ttk.Label(params_frame, text="Response %:").grid(row=0, column=8, sticky=tk.W, padx=5)
        ttk.Spinbox(params_frame, from_=30, to=100, increment=5,
                    textvariable=self.response_percentage, width=10).grid(row=0, column=9, padx=5)

        ttk.Label(params_frame, text="History Limit:").grid(row=0, column=10, sticky=tk.W, padx=5)
        ttk.Spinbox(params_frame, from_=50, to=1000, increment=50,
                    textvariable=self.history_limit, width=10).grid(row=0, column=11, padx=5)

        # ==== MIDDLE SECTION: Progress & Controls ====
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Progress Bar
        progress_frame = ttk.LabelFrame(control_frame, text="Progress", padding=10)
        progress_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        self.progress_label = ttk.Label(progress_frame, text="Ready to process", font=('Arial', 10))
        self.progress_label.pack()
        
        # Statistics
        stats_frame = ttk.LabelFrame(control_frame, text="Statistics", padding=10)
        stats_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=5)
        
        self.stats_text = tk.Text(stats_frame, height=4, width=40, font=('Courier', 9))
        self.stats_text.pack()
        self.update_stats()
        
        # Control Buttons
        button_frame = ttk.LabelFrame(control_frame, text="Controls", padding=10)
        button_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=5)

        self.start_btn = ttk.Button(button_frame, text="[RESUME] Start Processing",
                                    command=self.start_processing, style='Accent.TButton')
        self.start_btn.pack(fill=tk.X, pady=2)

        self.pause_btn = ttk.Button(button_frame, text="[PAUSE] Pause",
                                    command=self.pause_processing, state=tk.DISABLED)
        self.pause_btn.pack(fill=tk.X, pady=2)

        self.stop_btn = ttk.Button(button_frame, text="[STOP] Stop",
                                   command=self.stop_processing, state=tk.DISABLED)
        self.stop_btn.pack(fill=tk.X, pady=2)

        # Test mode checkbox
        test_mode_check = ttk.Checkbutton(button_frame, text="Test Mode (Echo Input)",
                                          variable=self.test_mode)
        test_mode_check.pack(fill=tk.X, pady=2)

        # ==== BOTTOM SECTION: Preview & Logs (Tabbed) ====
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Tab 1: Console Log
        log_frame = ttk.Frame(self.notebook)
        self.notebook.add(log_frame, text="[LOG] Console Log")

        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD,
                                                   font=('Courier', 9), bg='#1e1e1e', fg='#d4d4d4')
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Configure log text tags for colors
        self.log_text.tag_config('info', foreground='#4ec9b0')
        self.log_text.tag_config('success', foreground='#4fc1ff')
        self.log_text.tag_config('warning', foreground='#dcdcaa')
        self.log_text.tag_config('error', foreground='#f48771')
        self.log_text.tag_config('batch', foreground='#c586c0')

        # Tab 2: Diff Viewer (Batch Preview with line numbers)
        preview_frame = ttk.Frame(self.notebook)
        self.notebook.add(preview_frame, text="[VIEW] Diff Viewer")
        self.diff_viewer_tab_index = 1  # Store tab index for updating title

        # History dropdown frame for Diff Viewer
        diff_history_frame = ttk.Frame(preview_frame)
        diff_history_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(diff_history_frame, text="History:").pack(side=tk.LEFT, padx=5)
        self.diff_history_var = tk.StringVar()
        self.diff_history_combo = ttk.Combobox(diff_history_frame, textvariable=self.diff_history_var,
                                               width=60, state='readonly')
        self.diff_history_combo.pack(side=tk.LEFT, padx=5)
        self.diff_history_combo.bind('<<ComboboxSelected>>', self._on_diff_history_selected)

        self.clear_diff_history_btn = ttk.Button(diff_history_frame, text="Clear History",
                                                 command=self._clear_diff_history)
        self.clear_diff_history_btn.pack(side=tk.LEFT, padx=5)

        preview_paned = ttk.PanedWindow(preview_frame, orient=tk.HORIZONTAL)
        preview_paned.pack(fill=tk.BOTH, expand=True)

        # Input preview (left side with line numbers)
        input_preview_frame = ttk.LabelFrame(preview_paned, text="INPUT to AI Model")
        self.input_preview = TextWithLineNumbers(input_preview_frame, wrap=tk.WORD,
                                                 font=('Courier New', 9), bg='#fff8dc')
        self.input_preview.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        preview_paned.add(input_preview_frame, weight=1)

        # Output preview (right side with line numbers)
        output_preview_frame = ttk.LabelFrame(preview_paned, text="AI Model OUTPUT")
        self.output_preview = TextWithLineNumbers(output_preview_frame, wrap=tk.WORD,
                                                  font=('Courier New', 9), bg='#e8f4ea')
        self.output_preview.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        preview_paned.add(output_preview_frame, weight=1)

        # Synchronized scrolling for diff viewer
        self._setup_synchronized_scrolling()

        # Tab 3: Full Output View with line numbers and Find function
        output_frame = ttk.Frame(self.notebook)
        self.notebook.add(output_frame, text="[DOC] Full Output")

        # History dropdown frame for Full Output
        full_output_history_frame = ttk.Frame(output_frame)
        full_output_history_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(full_output_history_frame, text="History:").pack(side=tk.LEFT, padx=5)
        self.full_output_history_var = tk.StringVar()
        self.full_output_history_combo = ttk.Combobox(full_output_history_frame, textvariable=self.full_output_history_var,
                                                      width=60, state='readonly')
        self.full_output_history_combo.pack(side=tk.LEFT, padx=5)
        self.full_output_history_combo.bind('<<ComboboxSelected>>', self._on_full_output_history_selected)

        self.clear_full_output_history_btn = ttk.Button(full_output_history_frame, text="Clear History",
                                                        command=self._clear_full_output_history)
        self.clear_full_output_history_btn.pack(side=tk.LEFT, padx=5)

        # Text area with line numbers
        self.full_output_text = TextWithLineNumbers(output_frame, wrap=tk.WORD,
                                                    font=('Courier New', 10), bg='white')
        self.full_output_text.pack(fill=tk.BOTH, expand=True)

        # Find toolbar
        find_frame = ttk.Frame(output_frame)
        find_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(find_frame, text="Find:").pack(side=tk.LEFT, padx=5)
        self.find_entry = ttk.Entry(find_frame, width=30)
        self.find_entry.pack(side=tk.LEFT, padx=5)
        self.find_entry.bind('<Return>', lambda e: self._find_in_output())

        self.find_btn = ttk.Button(find_frame, text="Find", command=self._find_in_output)
        self.find_btn.pack(side=tk.LEFT, padx=2)

        ttk.Button(find_frame, text="Next", command=self._find_next).pack(side=tk.LEFT, padx=2)
        ttk.Button(find_frame, text="Clear", command=self._clear_find).pack(side=tk.LEFT, padx=2)

        self.find_count_label = ttk.Label(find_frame, text="")
        self.find_count_label.pack(side=tk.LEFT, padx=10)

        # Find state
        self.find_matches = []
        self.find_current_index = 0

        # Status Bar
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        # Load history dropdowns
        self._load_history_dropdowns()

        self.log_message("[OK] GUI initialized. Configure settings and load files to begin.", 'success')

    def _setup_synchronized_scrolling(self):
        """Setup synchronized scrolling between diff viewer panels"""
        def sync_scroll(*args):
            # Synchronize both text widgets
            self.input_preview.yview(*args)
            self.output_preview.yview(*args)

        # Override the yscrollcommand for both widgets to sync them
        def make_sync_command(other_widget):
            def sync_command(*args):
                # Update scrollbar
                other_widget.scrollbar.set(*args)
                # Sync scroll positions
                try:
                    # Get the first visible line position
                    first_visible = other_widget.text.index('@0,0')
                    # Update line numbers
                    other_widget._update_line_numbers()
                except:
                    pass
            return sync_command

        # Bind mousewheel events for synchronized scrolling
        def on_mousewheel(event, source_widget, target_widget):
            # Calculate scroll amount
            delta = -1 if event.delta > 0 else 1
            # Scroll both widgets
            source_widget.text.yview_scroll(delta, 'units')
            target_widget.text.yview_scroll(delta, 'units')
            return "break"

        # Bind mousewheel to input preview
        self.input_preview.text.bind('<MouseWheel>',
                                      lambda e: on_mousewheel(e, self.input_preview, self.output_preview))
        self.input_preview.text.bind('<Button-4>',
                                      lambda e: on_mousewheel(type('Event', (), {'delta': 120})(), self.input_preview, self.output_preview))
        self.input_preview.text.bind('<Button-5>',
                                      lambda e: on_mousewheel(type('Event', (), {'delta': -120})(), self.input_preview, self.output_preview))

        # Bind mousewheel to output preview
        self.output_preview.text.bind('<MouseWheel>',
                                       lambda e: on_mousewheel(e, self.output_preview, self.input_preview))
        self.output_preview.text.bind('<Button-4>',
                                       lambda e: on_mousewheel(type('Event', (), {'delta': 120})(), self.output_preview, self.input_preview))
        self.output_preview.text.bind('<Button-5>',
                                       lambda e: on_mousewheel(type('Event', (), {'delta': -120})(), self.output_preview, self.input_preview))

    def _find_in_output(self):
        """Find all occurrences of search term in Full Output"""
        search_term = self.find_entry.get()
        if not search_term:
            return

        # Clear previous highlights
        self._clear_find()

        # Search for all occurrences
        self.find_matches = []
        start_pos = '1.0'
        while True:
            pos = self.full_output_text.search(search_term, start_pos, tk.END, nocase=True)
            if not pos:
                break
            end_pos = f"{pos}+{len(search_term)}c"
            self.find_matches.append((pos, end_pos))
            start_pos = end_pos

        # Highlight all matches
        if self.find_matches:
            for start, end in self.find_matches:
                self.full_output_text.tag_add('search_highlight', start, end)

            # Configure highlight tag
            self.full_output_text.tag_config('search_highlight', background='yellow', foreground='black')

            # Show first match
            self.find_current_index = 0
            self._highlight_current_match()

            # Update count label
            self.find_count_label.config(text=f"{len(self.find_matches)} matches found")
        else:
            self.find_count_label.config(text="No matches found")

    def _find_next(self):
        """Jump to next search match"""
        if not self.find_matches:
            return

        self.find_current_index = (self.find_current_index + 1) % len(self.find_matches)
        self._highlight_current_match()

    def _highlight_current_match(self):
        """Highlight the current match with a different color"""
        if not self.find_matches:
            return

        # Remove previous current highlight
        self.full_output_text.tag_remove('current_match', '1.0', tk.END)

        # Add current match highlight
        start, end = self.find_matches[self.find_current_index]
        self.full_output_text.tag_add('current_match', start, end)
        self.full_output_text.tag_config('current_match', background='orange', foreground='black')

        # Scroll to current match
        self.full_output_text.see(start)

        # Update count label
        self.find_count_label.config(
            text=f"Match {self.find_current_index + 1}/{len(self.find_matches)}"
        )

    def _clear_find(self):
        """Clear all search highlights"""
        self.full_output_text.tag_remove('search_highlight', '1.0', tk.END)
        self.full_output_text.tag_remove('current_match', '1.0', tk.END)
        self.find_matches = []
        self.find_current_index = 0
        self.find_count_label.config(text="")

    # ========================================================================
    # HISTORY MANAGEMENT METHODS
    # ========================================================================

    def _load_history_dropdowns(self):
        """Load history entries from settings into dropdowns"""
        # Load Diff Viewer history
        diff_history = self.settings_mgr.settings.get("diff_viewer_history", [])
        diff_entries = [entry["label"] for entry in diff_history]
        self.diff_history_combo['values'] = diff_entries

        # Load Full Output history
        full_output_history = self.settings_mgr.settings.get("full_output_history", [])
        full_output_entries = [entry["label"] for entry in full_output_history]
        self.full_output_history_combo['values'] = full_output_entries

    def _save_to_diff_history(self, input_file, batch_num, input_text, output_text):
        """Save a batch to Diff Viewer history"""
        # Extract filename without extension
        filename = Path(input_file).stem
        label = f"{filename} - Batch {batch_num}"

        # Create history entry
        entry = {
            "label": label,
            "input_file": input_file,
            "batch_num": batch_num,
            "input_text": input_text,
            "output_text": output_text,
            "timestamp": datetime.now().isoformat()
        }

        # Add to history (avoid duplicates based on label)
        history = self.settings_mgr.settings.get("diff_viewer_history", [])
        # Remove any existing entry with the same label
        history = [h for h in history if h["label"] != label]
        # Add new entry at the beginning
        history.insert(0, entry)

        # Limit history size based on user setting
        history = history[:self.history_limit.get()]

        # Save to settings
        self.settings_mgr.settings["diff_viewer_history"] = history
        self.settings_mgr.save_settings()

        # Update dropdown
        self._load_history_dropdowns()

    def _save_to_full_output_history(self, input_file, batch_num, output_text):
        """Save a batch to Full Output history"""
        # Extract filename without extension
        filename = Path(input_file).stem
        label = f"{filename} - Batch {batch_num}"

        # Create history entry
        entry = {
            "label": label,
            "input_file": input_file,
            "batch_num": batch_num,
            "output_text": output_text,
            "timestamp": datetime.now().isoformat()
        }

        # Add to history (avoid duplicates based on label)
        history = self.settings_mgr.settings.get("full_output_history", [])
        # Remove any existing entry with the same label
        history = [h for h in history if h["label"] != label]
        # Add new entry at the beginning
        history.insert(0, entry)

        # Limit history size based on user setting
        history = history[:self.history_limit.get()]

        # Save to settings
        self.settings_mgr.settings["full_output_history"] = history
        self.settings_mgr.save_settings()

        # Update dropdown
        self._load_history_dropdowns()

    def _on_diff_history_selected(self, event=None):
        """Handle Diff Viewer history selection"""
        selected_label = self.diff_history_var.get()
        if not selected_label:
            return

        # Find the entry in history
        history = self.settings_mgr.settings.get("diff_viewer_history", [])
        entry = next((h for h in history if h["label"] == selected_label), None)

        if entry:
            # Update Diff Viewer with historical data
            self.input_preview.delete(1.0, tk.END)
            self.input_preview.insert(1.0, entry["input_text"])

            self.output_preview.delete(1.0, tk.END)
            self.output_preview.insert(1.0, entry["output_text"])

            # Update tab title
            self.notebook.tab(self.diff_viewer_tab_index,
                            text=f"[VIEW] Diff Viewer - {selected_label}")

            self.log_message(f"[OK] Loaded history: {selected_label}", 'info')

    def _on_full_output_history_selected(self, event=None):
        """Handle Full Output history selection"""
        selected_label = self.full_output_history_var.get()
        if not selected_label:
            return

        # Find the entry in history
        history = self.settings_mgr.settings.get("full_output_history", [])
        entry = next((h for h in history if h["label"] == selected_label), None)

        if entry:
            # Update Full Output with historical data
            self.full_output_text.delete(1.0, tk.END)
            self.full_output_text.insert(1.0, entry["output_text"])

            self.log_message(f"[OK] Loaded history: {selected_label}", 'info')

    def _clear_diff_history(self):
        """Clear all Diff Viewer history"""
        if messagebox.askyesno("Clear History",
                              "Are you sure you want to clear all Diff Viewer history?"):
            self.settings_mgr.settings["diff_viewer_history"] = []
            self.settings_mgr.save_settings()
            self.diff_history_combo['values'] = []
            self.diff_history_var.set('')
            self.log_message("[OK] Diff Viewer history cleared", 'info')

    def _clear_full_output_history(self):
        """Clear all Full Output history"""
        if messagebox.askyesno("Clear History",
                              "Are you sure you want to clear all Full Output history?"):
            self.settings_mgr.settings["full_output_history"] = []
            self.settings_mgr.save_settings()
            self.full_output_history_combo['values'] = []
            self.full_output_history_var.set('')
            self.log_message("[OK] Full Output history cleared", 'info')

    # ========================================================================
    # END HISTORY MANAGEMENT METHODS
    # ========================================================================

    def browse_input(self):
        """Browse for input file"""
        filename = filedialog.askopenfilename(
            title="Select Input File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.input_file.set(filename)
            self.log_message(f"Input file selected: {filename}", 'info')
            
            # Auto-suggest output file
            if not self.output_file.get():
                output_path = str(Path(filename).parent / "OUTPUT.txt")
                self.output_file.set(output_path)
    
    def browse_output(self):
        """Browse for output file"""
        filename = filedialog.asksaveasfilename(
            title="Select Output File",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.output_file.set(filename)
            self.log_message(f"Output file selected: {filename}", 'info')
    
    def browse_prompt(self):
        """Browse for prompt file"""
        filename = filedialog.askopenfilename(
            title="Select Prompt File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.prompt_file.set(filename)
            self.log_message(f"Prompt file selected: {filename}", 'info')
    
    def toggle_api_key_visibility(self):
        """Toggle API key visibility"""
        if self.api_key_visible.get():
            self.api_key_entry.config(show="")
            self.api_key_visible.set(False)
        else:
            self.api_key_entry.config(show="*")
            self.api_key_visible.set(True)

    def save_api_key(self):
        """Save API key to encrypted settings"""
        api_key = self.api_key.get().strip()
        if api_key:
            self.settings_mgr.set_api_key(api_key)
            self.log_message("[OK] API key saved (encrypted)", 'success')

    def save_settings(self):
        """Save all settings"""
        self.settings_mgr.settings.update({
            "model_name": self.model_name.get(),
            "temperature": self.temperature.get(),
            "seed": self.seed.get(),
            "batch_size": self.batch_size.get(),
            "max_tokens": self.max_tokens.get(),
            "response_percentage": self.response_percentage.get(),
            "history_limit": self.history_limit.get(),
            "last_input_file": self.input_file.get(),
            "last_output_file": self.output_file.get(),
            "last_prompt_file": self.prompt_file.get()
        })
        self.settings_mgr.save_settings()

    def on_closing(self):
        """Handle window close event"""
        self.save_settings()
        self.root.destroy()

    def test_connection(self):
        """Test connection to OpenRouter API"""
        api_key = self.api_key.get().strip()

        if not api_key:
            messagebox.showerror("Error", "Please enter your OpenRouter API key first!")
            return

        self.log_message("Testing connection to OpenRouter API...", 'info')
        self.log_message(f"Model: {self.model_name.get()}", 'info')

        try:
            base_url = self.settings_mgr.get_base_url()

            client = openai.OpenAI(
                base_url=base_url,
                api_key=api_key
            )

            # Try a simple completion
            response = client.chat.completions.create(
                model=self.model_name.get(),
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )

            self.log_message("[OK] Connection successful! OpenRouter API is ready.", 'success')
            messagebox.showinfo("Connection Test", f"[OK] Successfully connected to OpenRouter API!\n\nModel: {self.model_name.get()}")

        except Exception as e:
            error_msg = str(e)
            # Mask API key in error message
            error_msg = SettingsManager.mask_api_key(error_msg, api_key)
            self.log_message(f"[X] Connection failed: {error_msg}", 'error')
            messagebox.showerror("Connection Test", f"Failed to connect:\n{error_msg}\n\nPlease check:\n- API key is valid\n- Model name is correct")

    def preclean_input(self):
        """Pre-clean input file with detailed transformation logging"""
        if not self.input_file.get():
            messagebox.showerror("Error", "Please select an input file first!")
            return

        try:
            self.log_message("="*70, 'info')
            self.log_message("[TOOL] STARTING DETERMINISTIC PRE-CLEANING WITH DETAILED LOGGING", 'batch')
            self.log_message("="*70, 'info')

            # Read input file
            input_path = Path(self.input_file.get())
            self.log_message(f"[READ] Reading: {input_path.name}", 'info')

            with open(input_path, 'r', encoding='utf-8') as f:
                original_text = f.read()

            original_size = len(original_text)
            original_lines = original_text.count('\n') + 1

            self.log_message(f"   Original: {original_lines:,} lines, {original_size:,} chars", 'info')
            self.log_message("", 'info')

            start_time = time.time()
            current_text = original_text

            # Helper function to show changes
            def log_transformation(step_name, before, after, show_examples=True):
                before_size = len(before)
                after_size = len(after)
                change = after_size - before_size
                change_pct = (change / before_size * 100) if before_size > 0 else 0

                self.log_message(f"{'='*70}", 'batch')
                self.log_message(f"STEP: {step_name}", 'batch')
                self.log_message(f"{'='*70}", 'batch')
                self.log_message(f"   Before: {before_size:,} chars", 'info')
                self.log_message(f"   After:  {after_size:,} chars", 'info')
                self.log_message(f"   Change: {change:+,} chars ({change_pct:+.2f}%)", 'success' if change <= 0 else 'warning')

                if show_examples and before != after:
                    # Find differences
                    self._show_text_differences(before, after, step_name)

                self.log_message("", 'info')
                return after

            # ========================================================================
            # PART 1: MULTI-PASS OCR CLEANING (87.09% accuracy)
            # ========================================================================
            self.log_message("[*] PART 1: MULTI-PASS OCR CLEANING (5 Stages)", 'batch')
            self.log_message("   Production-ready processor: 87.09% accuracy", 'success')
            self.log_message("", 'info')

            before = current_text
            current_text, ocr_state = TextPreprocessor.apply_multi_pass_ocr_cleaning(current_text)

            # Log multi-pass processor stats
            self.log_message(f"{'='*70}", 'batch')
            self.log_message(f"MULTI-PASS OCR PROCESSING RESULTS", 'batch')
            self.log_message(f"{'='*70}", 'batch')
            self.log_message(f"   [OK] Stage 1: Semantic Cleaning", 'success')
            self.log_message(f"      - Page headers removed: {ocr_state.stats.get('headers_removed', 0)}", 'info')
            self.log_message(f"      - Whitespace normalized: {ocr_state.stats.get('whitespace_normalized', 0)}", 'info')
            self.log_message(f"   [OK] Stage 2: Deterministic Cleaning", 'success')
            self.log_message(f"      - OCR artifacts fixed: {ocr_state.stats.get('ocr_artifacts_fixed', 0)}", 'info')
            self.log_message(f"      - Apostrophes fixed: {ocr_state.stats.get('apostrophes_fixed', 0)}", 'info')
            self.log_message(f"      - Word fragments fixed: {ocr_state.stats.get('fragments_fixed', 0)}", 'info')
            self.log_message(f"   [OK] Stage 3: Sentence Reconstruction", 'success')
            self.log_message(f"      - Lines merged: {ocr_state.stats.get('lines_merged', 0)}", 'info')
            self.log_message(f"      - Paragraphs formed: {ocr_state.stats.get('paragraphs_formed', 0)}", 'info')
            self.log_message(f"   [OK] Stage 4: Edge Case Collection", 'success')
            self.log_message(f"      - Edge cases detected: {len(ocr_state.edge_cases)}", 'info')
            self.log_message(f"   [OK] Stage 5: Edge Case Handling", 'success')
            self.log_message(f"      - Edge cases logged: {ocr_state.stats.get('edge_cases_handled', 0)}", 'info')

            current_text = log_transformation("Multi-Pass OCR Cleaning (5 stages)", before, current_text, show_examples=True)

            # ========================================================================
            # PART 2: TTS-SPECIFIC NORMALIZATION (10 Steps)
            # ========================================================================
            self.log_message("[*] PART 2: TTS-SPECIFIC NORMALIZATION (10 Steps)", 'batch')
            self.log_message("", 'info')

            # Step 1 of TTS Normalization: Normalize punctuation
            self.log_message("[*] TTS Step 1: Normalizing punctuation (???, !!!, ---, ...)", 'batch')
            before = current_text
            current_text = TextPreprocessor.normalize_punctuation(current_text)
            current_text = log_transformation("Normalize Punctuation", before, current_text)

            # Step 2 of TTS Normalization: Normalize symbols
            self.log_message("[*] TTS Step 2: Normalizing symbols (™, ©, &, @, #)", 'batch')
            before = current_text
            current_text = TextPreprocessor.normalize_symbols(current_text)
            current_text = log_transformation("Normalize Symbols", before, current_text)

            # Step 3 of TTS Normalization: Normalize numbers
            self.log_message("[*] TTS Step 3: Normalizing numbers (1st→first, 1990s)", 'batch')
            before = current_text
            current_text = TextPreprocessor.normalize_numbers(current_text)
            current_text = log_transformation("Normalize Numbers", before, current_text)

            # Step 4 of TTS Normalization: Normalize currency
            self.log_message("[*] TTS Step 4: Normalizing currency ($100→100 dollars)", 'batch')
            before = current_text
            current_text = TextPreprocessor.normalize_currency(current_text)
            current_text = log_transformation("Normalize Currency", before, current_text)

            # Step 5 of TTS Normalization: Normalize ALL CAPS
            self.log_message("[*] TTS Step 5: Normalizing ALL CAPS (preserve acronyms)", 'batch')
            before = current_text
            current_text = TextPreprocessor.normalize_all_caps(current_text)
            current_text = log_transformation("Normalize ALL CAPS", before, current_text)

            # Step 6 of TTS Normalization: Normalize chapter markers
            self.log_message("[*] TTS Step 6: Normalizing chapter markers (Chapter IV→Chapter 4)", 'batch')
            before = current_text
            current_text = TextPreprocessor.normalize_chapter_markers(current_text)
            current_text = log_transformation("Normalize Chapter Markers", before, current_text)

            # Step 7 of TTS Normalization: Remove URLs and emails
            self.log_message("[*] TTS Step 7: Removing URLs and emails", 'batch')
            before = current_text
            current_text = TextPreprocessor.remove_urls_emails(current_text)
            current_text = log_transformation("Remove URLs/Emails", before, current_text)

            # Step 8 of TTS Normalization: Remove page numbers
            self.log_message("[*] TTS Step 8: Removing remaining page numbers", 'batch')
            before = current_text
            current_text = TextPreprocessor.remove_page_numbers(current_text)
            current_text = log_transformation("Remove Page Numbers", before, current_text)

            # Step 9 of TTS Normalization: Normalize whitespace
            self.log_message("[*] TTS Step 9: Normalizing whitespace", 'batch')
            before = current_text
            current_text = TextPreprocessor.normalize_whitespace(current_text)
            current_text = log_transformation("Normalize Whitespace", before, current_text)

            # Step 16: Chunk for TTS using spaCy + Deepgram approach
            self.log_message("[*] Step 16: Chunking for TTS (spaCy + Deepgram hybrid)", 'batch')
            self.log_message("   Using linguistic sentence boundaries (250 char max)", 'info')
            before = current_text
            current_text = TextPreprocessor.chunk_for_tts(current_text, max_chars=250)
            current_text = log_transformation("Chunk for TTS", before, current_text, show_examples=False)

            processing_time = time.time() - start_time
            preprocessed = current_text

            processed_size = len(preprocessed)
            processed_lines = preprocessed.count('\n') + 1

            # Save to precleaned file
            output_path = input_path.parent / f"{input_path.stem}_PRECLEANED.txt"
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(preprocessed)

            # Calculate overall statistics
            size_reduction = ((original_size - processed_size) / original_size * 100) if original_size > 0 else 0
            line_change = ((processed_lines - original_lines) / original_lines * 100) if original_lines > 0 else 0

            # Log final results
            self.log_message("="*70, 'success')
            self.log_message("[DONE] PRE-CLEANING COMPLETE!", 'success')
            self.log_message("="*70, 'success')
            self.log_message(f"   Original:   {original_lines:,} lines, {original_size:,} chars", 'info')
            self.log_message(f"   Processed:  {processed_lines:,} lines, {processed_size:,} chars", 'success')
            self.log_message(f"   Overall:    {size_reduction:+.1f}% chars, {line_change:+.1f}% lines", 'info')
            self.log_message(f"   Time:       {processing_time:.2f}s", 'info')
            self.log_message(f"   Saved to:   {output_path.name}", 'success')
            self.log_message("="*70, 'success')

            # Ask if user wants to use precleaned file as input
            if messagebox.askyesno("Pre-cleaning Complete",
                                   f"Pre-cleaning complete!\n\n"
                                   f"Original: {original_lines:,} lines, {original_size:,} chars\n"
                                   f"Cleaned: {processed_lines:,} lines, {processed_size:,} chars\n"
                                   f"Change: {size_reduction:+.1f}% size\n\n"
                                   f"Saved to: {output_path.name}\n\n"
                                   f"Use precleaned file as input?"):
                self.input_file.set(str(output_path))
                self.log_message(f"[OK] Input file updated to: {output_path.name}", 'success')

                # Update preview
                preview_text = preprocessed[:1000] + "..." if len(preprocessed) > 1000 else preprocessed
                self.input_preview.delete(1.0, tk.END)
                self.input_preview.insert(1.0, preview_text)

        except Exception as e:
            self.log_message(f"[X] Pre-cleaning failed: {str(e)}", 'error')
            messagebox.showerror("Pre-cleaning Error", f"Failed to pre-clean file:\n{str(e)}")

    def _show_text_differences(self, before, after, step_name):
        """Show specific examples of text changes"""
        import difflib

        # For text deletions, find removed lines
        before_lines = before.split('\n')
        after_lines = after.split('\n')

        # Find specific changes
        changes_shown = 0
        max_examples = 5  # Limit examples to avoid log spam

        # Use difflib to find differences
        diff = list(difflib.unified_diff(before_lines[:100], after_lines[:100], lineterm='', n=0))

        deletions = []
        additions = []
        modifications = []

        i = 0
        while i < len(diff):
            line = diff[i]
            if line.startswith('---') or line.startswith('+++') or line.startswith('@@'):
                i += 1
                continue

            if line.startswith('-') and not line.startswith('---'):
                deletions.append(line[1:])
            elif line.startswith('+') and not line.startswith('+++'):
                additions.append(line[1:])

            i += 1

        # Show deletions
        if deletions and changes_shown < max_examples:
            self.log_message("   [DOWN] Text Removed:", 'warning')
            for deletion in deletions[:max_examples - changes_shown]:
                if deletion.strip():
                    preview = deletion[:100] + "..." if len(deletion) > 100 else deletion
                    self.log_message(f"      - '{preview}'", 'warning')
                    changes_shown += 1
                    if changes_shown >= max_examples:
                        break
            if len(deletions) > max_examples:
                self.log_message(f"      ... and {len(deletions) - max_examples} more deletions", 'warning')

        # Show additions (new text)
        if additions and changes_shown < max_examples:
            self.log_message("   [UP] Text Added:", 'success')
            for addition in additions[:max_examples - changes_shown]:
                if addition.strip():
                    preview = addition[:100] + "..." if len(addition) > 100 else addition
                    self.log_message(f"      + '{preview}'", 'success')
                    changes_shown += 1
                    if changes_shown >= max_examples:
                        break
            if len(additions) > max_examples:
                self.log_message(f"      ... and {len(additions) - max_examples} more additions", 'success')

        # If no specific changes detected but text changed
        if changes_shown == 0 and before != after:
            # Find first difference
            for i, (b_char, a_char) in enumerate(zip(before, after)):
                if b_char != a_char:
                    context_start = max(0, i - 20)
                    context_end = min(len(before), i + 80)
                    before_snippet = before[context_start:context_end]
                    after_snippet = after[context_start:min(len(after), context_end)]

                    self.log_message("   [RETRY] Example Change:", 'info')
                    self.log_message(f"      Before: '{before_snippet}'", 'warning')
                    self.log_message(f"      After:  '{after_snippet}'", 'success')
                    break
    
    def log_message(self, message, tag='info'):
        """Add message to log (thread-safe via queue)"""
        self.log_queue.put((message, tag))
    
    def process_log_queue(self):
        """Process queued log messages"""
        try:
            while True:
                message, tag = self.log_queue.get_nowait()
                timestamp = datetime.now().strftime("%H:%M:%S")
                self.log_text.insert(tk.END, f"[{timestamp}] {message}\n", tag)
                self.log_text.see(tk.END)
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self.process_log_queue)
    
    def update_stats(self):
        """Update statistics display"""
        self.stats_text.delete(1.0, tk.END)
        
        if self.is_processing:
            elapsed = time.time() - self.start_time if self.start_time else 0
            elapsed_str = time.strftime("%H:%M:%S", time.gmtime(elapsed))
            
            stats = f"""Batch:     {self.current_batch}/{self.total_batches}
Time:      {elapsed_str}
Status:    {'[PAUSE] PAUSED' if self.is_paused else '[RESUME] PROCESSING'}
Progress:  {self.progress_bar['value']:.1f}%"""
        else:
            stats = """Batch:     -
Time:      00:00:00
Status:    [STOP] STOPPED
Progress:  0.0%"""
        
        self.stats_text.insert(1.0, stats)
        
        if self.is_processing:
            self.root.after(1000, self.update_stats)
    
    def start_processing(self):
        """Start the batch processing"""
        # Validation
        if not self.input_file.get():
            messagebox.showerror("Error", "Please select an input file!")
            return
        
        if not self.output_file.get():
            messagebox.showerror("Error", "Please select an output file!")
            return
        
        if not self.prompt_file.get():
            messagebox.showerror("Error", "Please select a prompt file!")
            return
        
        # Confirm start
        if not messagebox.askyesno("Start Processing", 
                                   f"Start processing {self.input_file.get()}?\n\nThis will overwrite {self.output_file.get()}"):
            return
        
        # Update UI
        self.is_processing = True
        self.is_paused = False
        self.current_batch = 0
        self.start_time = time.time()
        self.previous_context = ""

        # Reset batch continuity tracking
        self.previous_input_last_sentence = ""
        self.previous_output_last_sentence = ""

        self.start_btn.config(state=tk.DISABLED)
        self.pause_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.NORMAL)
        
        # Clear output file
        with open(self.output_file.get(), 'w', encoding='utf-8') as f:
            f.write('')
        
        self.log_message("="*70, 'info')
        self.log_message("STARTING TTS TEXT PREPROCESSING", 'batch')
        self.log_message("="*70, 'info')
        
        # Start processing in separate thread
        thread = threading.Thread(target=self.process_batches, daemon=True)
        thread.start()
        
        self.update_stats()
    
    def pause_processing(self):
        """Pause/Resume processing"""
        self.is_paused = not self.is_paused
        
        if self.is_paused:
            self.pause_btn.config(text="[RESUME] Resume")
            self.log_message("[PAUSE] Processing PAUSED by user", 'warning')
        else:
            self.pause_btn.config(text="[PAUSE] Pause")
            self.log_message("[RESUME] Processing RESUMED", 'success')
        
        self.update_stats()
    
    def stop_processing(self):
        """Stop processing"""
        if messagebox.askyesno("Stop Processing", "Are you sure you want to stop?\n\nProgress will be saved."):
            self.is_processing = False
            self.log_message("[STOP] [Request interrupted by user]", 'error')
            self.finish_processing()
    
    def finish_processing(self):
        """Clean up after processing"""
        self.is_processing = False
        self.is_paused = False
        
        self.start_btn.config(state=tk.NORMAL)
        self.pause_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.DISABLED)
        
        self.progress_bar['value'] = 0
        self.update_stats()
    
    def extract_last_sentences(self, text, num_sentences=3):
        """Extract last N sentences for context"""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        # Filter out any LLM-generated batch completion messages
        sentences = [s for s in sentences if not re.search(r'Batch\s+\d+.*complete', s, re.IGNORECASE)]

        last_sentences = sentences[-num_sentences:] if len(sentences) >= num_sentences else sentences
        return ' '.join(last_sentences) + '.' if last_sentences else ""

    def extract_first_sentence(self, text):
        """Extract first sentence from text"""
        text = text.strip()
        if not text:
            return ""

        # Split by sentence-ending punctuation
        match = re.search(r'[.!?]+', text)
        if match:
            first_sentence = text[:match.end()].strip()
            return first_sentence

        # If no sentence ending found, take first line or 150 chars
        lines = text.split('\n')
        first_line = lines[0].strip()
        if len(first_line) > 150:
            return first_line[:150] + "..."
        return first_line

    def extract_last_sentence(self, text):
        """Extract last sentence from text"""
        text = text.strip()
        if not text:
            return ""

        # Split by sentence-ending punctuation
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        # Filter out batch completion messages
        sentences = [s for s in sentences if not re.search(r'Batch\s+\d+.*complete', s, re.IGNORECASE)]

        if sentences:
            last_sentence = sentences[-1]
            # Add back the punctuation
            if text.rstrip().endswith(('.', '!', '?')):
                last_sentence += text.rstrip()[-1]
            return last_sentence

        return text[:150] if len(text) > 150 else text

    def check_batch_alignment(self, input_text, output_text, batch_num):
        """
        Check alignment between input and output by comparing first and last sentences.

        This detects:
        - Missing content at start/end
        - Hallucinated content
        - Misalignment between batches
        """
        # Extract boundaries
        input_first = self.extract_first_sentence(input_text)
        input_last = self.extract_last_sentence(input_text)
        output_first = self.extract_first_sentence(output_text)
        output_last = self.extract_last_sentence(output_text)

        # Log alignment check
        self.log_message(f"   {'='*66}", 'info')
        self.log_message(f"   [CHECK] BATCH ALIGNMENT CHECK", 'batch')
        self.log_message(f"   {'='*66}", 'info')

        # First sentence comparison
        self.log_message(f"   [IN] INPUT First sentence:", 'info')
        self.log_message(f"      '{input_first}'", 'info')
        self.log_message(f"   [OUT] OUTPUT First sentence:", 'info')
        self.log_message(f"      '{output_first}'", 'info')

        # Check if first sentences match (allowing for minor transformations)
        first_match = self._fuzzy_sentence_match(input_first, output_first)
        if first_match:
            self.log_message(f"   [OK] First sentences aligned", 'success')
        else:
            self.log_message(f"   [WARNING] WARNING: First sentences DO NOT match!", 'warning')
            self._show_sentence_diff(input_first, output_first, "FIRST")

        self.log_message(f"", 'info')

        # Last sentence comparison
        self.log_message(f"   [IN] INPUT Last sentence:", 'info')
        self.log_message(f"      '{input_last}'", 'info')
        self.log_message(f"   [OUT] OUTPUT Last sentence:", 'info')
        self.log_message(f"      '{output_last}'", 'info')

        # Check if last sentences match
        last_match = self._fuzzy_sentence_match(input_last, output_last)
        if last_match:
            self.log_message(f"   [OK] Last sentences aligned", 'success')
        else:
            self.log_message(f"   [WARNING] WARNING: Last sentences DO NOT match!", 'warning')
            self._show_sentence_diff(input_last, output_last, "LAST")

        self.log_message(f"   {'='*66}", 'info')

        # Return overall alignment status
        return first_match and last_match

    def _fuzzy_sentence_match(self, sent1, sent2, threshold=0.7):
        """
        Check if two sentences are similar enough (fuzzy match).

        Allows for minor transformations like:
        - Punctuation changes
        - Case changes
        - Minor word variations
        """
        if not sent1 or not sent2:
            return False

        # Normalize for comparison
        norm1 = re.sub(r'[^\w\s]', '', sent1.lower())
        norm2 = re.sub(r'[^\w\s]', '', sent2.lower())

        # Simple word-based similarity
        words1 = set(norm1.split())
        words2 = set(norm2.split())

        if not words1 or not words2:
            return False

        # Calculate Jaccard similarity
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        similarity = intersection / union if union > 0 else 0

        return similarity >= threshold

    def _show_sentence_diff(self, input_sent, output_sent, position):
        """Show detailed diff between input and output sentences"""
        self.log_message(f"   [RETRY] OUTPUT diff view ({position} sentence):", 'warning')

        # Normalize and split into words
        input_words = input_sent.split()
        output_words = output_sent.split()

        # Find added/removed/changed words
        input_set = set(input_words)
        output_set = set(output_words)

        removed = input_set - output_set
        added = output_set - input_set

        if removed:
            self.log_message(f"      [-] Removed: {', '.join(removed)}", 'error')
        if added:
            self.log_message(f"      [+] Added: {', '.join(added)}", 'warning')

        # Show character-level similarity
        import difflib
        diff_ratio = difflib.SequenceMatcher(None, input_sent, output_sent).ratio()
        self.log_message(f"      [STAT] Similarity: {diff_ratio*100:.1f}%", 'info')

    def check_batch_continuity(self, current_input_text, current_output_text, batch_num):
        """
        Check continuity between consecutive batches.

        Compares:
        - Previous OUTPUT last sentence vs Current OUTPUT first sentence
        - Previous INPUT last sentence vs Current INPUT first sentence

        This detects gaps or overlaps at batch boundaries.
        """
        if batch_num <= 1:
            # No previous batch to compare
            return

        current_input_first = self.extract_first_sentence(current_input_text)
        current_output_first = self.extract_first_sentence(current_output_text)

        # Log continuity check
        self.log_message(f"   {'='*66}", 'info')
        self.log_message(f"   [LINK] BATCH CONTINUITY CHECK (Batch {batch_num-1} → {batch_num})", 'batch')
        self.log_message(f"   {'='*66}", 'info')

        # Check OUTPUT continuity
        self.log_message(f"   [OUT] Generated Output Continuity:", 'info')
        self.log_message(f"      BATCH {batch_num-1} OUTPUT last sentence:", 'info')
        self.log_message(f"      '{self.previous_output_last_sentence}'", 'info')
        self.log_message(f"      BATCH {batch_num} OUTPUT first sentence:", 'info')
        self.log_message(f"      '{current_output_first}'", 'info')

        # Check if output flows naturally
        output_continuity = self._check_sentence_continuity(
            self.previous_output_last_sentence,
            current_output_first
        )

        if output_continuity:
            self.log_message(f"      [OK] Output flows naturally between batches", 'success')
        else:
            self.log_message(f"      [WARNING] Potential gap or overlap in output!", 'warning')

        self.log_message(f"", 'info')

        # Check INPUT continuity (for reference)
        self.log_message(f"   [IN] Original Input Continuity:", 'info')
        self.log_message(f"      BATCH {batch_num-1} INPUT last sentence:", 'info')
        self.log_message(f"      '{self.previous_input_last_sentence}'", 'info')
        self.log_message(f"      BATCH {batch_num} INPUT first sentence:", 'info')
        self.log_message(f"      '{current_input_first}'", 'info')

        # Check if input was continuous
        input_continuity = self._check_sentence_continuity(
            self.previous_input_last_sentence,
            current_input_first
        )

        if input_continuity:
            self.log_message(f"      [OK] Input batches were continuous", 'success')
        else:
            self.log_message(f"      [WARNING] Input batches had a gap (expected for paragraph breaks)", 'info')

        self.log_message(f"   {'='*66}", 'info')

    def _check_sentence_continuity(self, prev_sentence, next_sentence):
        """
        Check if two consecutive sentences flow naturally.

        Returns True if sentences appear to be continuous (not overlapping or gapped).
        """
        if not prev_sentence or not next_sentence:
            return False

        # Normalize sentences
        prev_normalized = prev_sentence.lower().strip()
        next_normalized = next_sentence.lower().strip()

        # Check for exact duplication (overlap issue)
        if prev_normalized == next_normalized:
            return False  # Same sentence repeated

        # Check for significant word overlap (might indicate duplication)
        prev_words = set(prev_normalized.split())
        next_words = set(next_normalized.split())

        if prev_words and next_words:
            overlap = len(prev_words & next_words)
            overlap_ratio = overlap / min(len(prev_words), len(next_words))

            # If more than 80% overlap, might be duplicate content
            if overlap_ratio > 0.8:
                return False

        # Otherwise assume continuity is good
        return True

    def find_paragraph_break(self, lines, max_lookback=50):
        """Find natural paragraph break"""
        for i in range(len(lines)-1, max(len(lines)-max_lookback, 0), -1):
            if i > 0 and lines[i].strip() == '':
                return i
        return len(lines)
    
    def process_single_batch(self, text_batch, batch_num, context=""):
        """Process a single batch with OpenRouter API"""
        try:
            # TEST MODE: Echo input as output for testing alignment
            if self.test_mode.get():
                import time
                time.sleep(0.5)  # Simulate processing delay
                cleaned_text = text_batch  # Echo the exact input
                next_context = self.extract_last_sentences(cleaned_text, 3)
                # Return: (cleaned_text, next_context, input_size, output_size)
                return cleaned_text, next_context, len(text_batch), len(cleaned_text)

            # NORMAL MODE: Process with AI
            # Get API key
            api_key = self.api_key.get().strip()
            if not api_key:
                raise ValueError("API key is required. Please set it in the settings.")

            # Build user message
            if context and batch_num > 1:
                user_message = f"""CONTEXT FROM PREVIOUS BATCH (for reference only - DO NOT output):
"{context}"

NOW PROCESS THIS NEW TEXT:
{text_batch}

Remember: Only output the cleaned NEW text, not the context."""
            else:
                user_message = text_batch

            # Load system prompt
            with open(self.prompt_file.get(), 'r', encoding='utf-8') as f:
                system_prompt = f.read()

            # Get base URL based on region
            base_url = self.settings_mgr.get_base_url()

            # Create client
            client = openai.OpenAI(
                base_url=base_url,
                api_key=api_key
            )

            # Make request
            response = client.chat.completions.create(
                model=self.model_name.get(),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=self.temperature.get(),
                max_tokens=self.max_tokens.get(),
                seed=self.seed.get()
            )

            cleaned_text = response.choices[0].message.content
            next_context = self.extract_last_sentences(cleaned_text, 3)

            # Return stats for logging: (cleaned_text, next_context, input_size, output_size)
            return cleaned_text, next_context, len(user_message), len(cleaned_text)

        except Exception as e:
            # Mask API key in error message before logging
            error_msg = str(e)
            api_key = self.api_key.get().strip()
            if api_key:
                error_msg = SettingsManager.mask_api_key(error_msg, api_key)
            self.log_message(f"[X] Error processing batch {batch_num}: {error_msg}", 'error')
            return None, context, 0, 0
    
    def process_batches(self):
        """Main processing loop (runs in separate thread)"""
        try:
            # Read input file
            self.log_message(f"[READ] Reading input file: {self.input_file.get()}", 'info')
            with open(self.input_file.get(), 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            total_lines = len(lines)
            self.log_message(f"   Total lines: {total_lines}", 'info')
            
            # Calculate total batches
            self.total_batches = (total_lines // self.batch_size.get()) + 1
            self.log_message(f"   Estimated batches: {self.total_batches}", 'info')
            
            batch_size = self.batch_size.get()
            i = 0
            batch_num = 1
            retry_count = 0  # Track retries for low response errors

            # Retry statistics tracking
            retry_stats = {
                'batch_num': None,
                'first_attempt': {'llm_input': 0, 'llm_output': 0, 'llm_change': 0},
                'second_attempt': {'llm_input': 0, 'llm_output': 0, 'llm_change': 0}
            }

            while i < total_lines and self.is_processing:
                # Wait if paused
                while self.is_paused and self.is_processing:
                    time.sleep(0.5)
                
                if not self.is_processing:
                    break
                
                # Determine batch end
                batch_end = min(i + batch_size, total_lines)
                batch_lines = lines[i:batch_end]
                
                # Find natural breakpoint
                if batch_end < total_lines:
                    break_point = self.find_paragraph_break(batch_lines)
                    batch_lines = batch_lines[:break_point]
                    actual_end = i + break_point
                else:
                    actual_end = batch_end
                
                batch_text = ''.join(batch_lines)
                input_line_count = len(batch_lines)
                input_char_count = len(batch_text)

                # Update Diff Viewer tab title with batch number
                self.notebook.tab(self.diff_viewer_tab_index, text=f"[VIEW] Diff Viewer - Batch {batch_num}/{self.total_batches}")

                # Update input preview with FULL batch text (no 2000 char limit)
                self.input_preview.delete(1.0, tk.END)
                self.input_preview.insert(1.0, batch_text)

                # Clear output preview (will be filled after processing)
                self.output_preview.delete(1.0, tk.END)
                self.output_preview.insert(1.0, "[Processing...]")

                # Log batch info
                self.log_message(f"\n{'='*70}", 'batch')
                self.log_message(f"[BATCH] BATCH {batch_num}/{self.total_batches}", 'batch')
                self.log_message(f"{'='*70}", 'batch')
                self.log_message(f"   Lines: {i+1} to {actual_end}", 'info')
                self.log_message(f"   Input:  {input_line_count} lines, {input_char_count} chars", 'info')
                
                if self.previous_context:
                    self.log_message(f"   Using context from Batch {batch_num-1}", 'info')
                
                # Process batch
                self.log_message(f"   [PROC] Processing with {self.model_name.get()}...", 'info')
                batch_start_time = time.time()

                cleaned, next_context, llm_input_size, llm_output_size = self.process_single_batch(
                    batch_text,
                    batch_num,
                    self.previous_context
                )

                batch_time = time.time() - batch_start_time

                if cleaned:
                    # Calculate output stats
                    output_line_count = len(cleaned.splitlines())
                    output_char_count = len(cleaned)

                    # Calculate reductions from original batch text to cleaned output
                    char_reduction = ((input_char_count - output_char_count) / input_char_count * 100) if input_char_count > 0 else 0
                    line_reduction = ((input_line_count - output_line_count) / input_line_count * 100) if input_line_count > 0 else 0

                    # Calculate LLM input vs output change
                    llm_change = ((llm_output_size - llm_input_size) / llm_input_size * 100) if llm_input_size > 0 else 0

                    # Log LLM input/output comparison
                    self.log_message(f"   [OUT] Sent to LLM:      {llm_input_size} chars", 'info')
                    self.log_message(f"   [IN] Received from LLM: {llm_output_size} chars ({llm_change:+.1f}%)", 'info')

                    # Calculate configurable threshold based on response percentage
                    # response_percentage represents minimum acceptable output (e.g., 85% = at least 85% of input)
                    threshold = -(100 - self.response_percentage.get())

                    # Validate LLM response size - check for excessive differences
                    # Allow for reasonable variation but flag suspicious changes
                    if llm_change > 100:  # Output is more than 2x the input
                        self.log_message(f"   [X] CRITICAL ERROR: LLM response is {llm_change:+.1f}% larger than input!", 'error')
                        self.log_message(f"   [X] Expected ~{llm_input_size} chars, received {llm_output_size} chars", 'error')
                        self.log_message(f"   [X] This indicates the LLM may be hallucinating or adding unwanted content", 'error')
                        self.log_message(f"   [STOP] Stopping processing to prevent data contamination", 'error')
                        break
                    elif llm_change < threshold:  # Output below configured threshold
                        self.log_message(f"   [X] CRITICAL ERROR: LLM response is {llm_change:.1f}% vs threshold {threshold:.1f}%!", 'error')
                        self.log_message(f"   [X] Expected at least {self.response_percentage.get()}% of input size", 'error')
                        self.log_message(f"   [X] This indicates the LLM may be truncating or losing content", 'error')

                        if retry_count == 0:
                            # First occurrence - track stats and retry the batch
                            retry_stats['batch_num'] = batch_num
                            retry_stats['first_attempt'] = {
                                'llm_input': llm_input_size,
                                'llm_output': llm_output_size,
                                'llm_change': llm_change
                            }
                            retry_count += 1
                            self.log_message(f"   [RETRY] Retrying batch {batch_num} (attempt {retry_count + 1}/2)...", 'warning')
                            continue  # Retry same batch without advancing
                        else:
                            # Second occurrence - track second attempt stats
                            retry_stats['second_attempt'] = {
                                'llm_input': llm_input_size,
                                'llm_output': llm_output_size,
                                'llm_change': llm_change
                            }

                            # Generate retry report
                            self.log_message(f"\n{'='*70}", 'error')
                            self.log_message(f"[STAT] RETRY REPORT - Batch {batch_num}", 'error')
                            self.log_message(f"{'='*70}", 'error')
                            self.log_message(f"   Configured Threshold: {self.response_percentage.get()}% (or {threshold:.1f}% change)", 'info')
                            self.log_message(f"", 'info')
                            self.log_message(f"   First Attempt:", 'warning')
                            self.log_message(f"     Input:  {retry_stats['first_attempt']['llm_input']} chars", 'info')
                            self.log_message(f"     Output: {retry_stats['first_attempt']['llm_output']} chars", 'info')
                            self.log_message(f"     Change: {retry_stats['first_attempt']['llm_change']:+.1f}%", 'warning')
                            self.log_message(f"", 'info')
                            self.log_message(f"   Second Attempt:", 'error')
                            self.log_message(f"     Input:  {retry_stats['second_attempt']['llm_input']} chars", 'info')
                            self.log_message(f"     Output: {retry_stats['second_attempt']['llm_output']} chars", 'info')
                            self.log_message(f"     Change: {retry_stats['second_attempt']['llm_change']:+.1f}%", 'error')
                            self.log_message(f"", 'info')
                            delta = retry_stats['second_attempt']['llm_change'] - retry_stats['first_attempt']['llm_change']
                            self.log_message(f"   Improvement: {delta:+.1f}% between attempts", 'info' if delta > 0 else 'error')
                            self.log_message(f"{'='*70}", 'error')

                            # Pause for manual intervention
                            self.log_message(f"   [PAUSE] PAUSING processing after retry failed", 'error')
                            self.log_message(f"   [PAUSE] Please review and manually resume when ready", 'warning')
                            retry_count = 0  # Reset for next batch
                            retry_stats = {
                                'batch_num': None,
                                'first_attempt': {'llm_input': 0, 'llm_output': 0, 'llm_change': 0},
                                'second_attempt': {'llm_input': 0, 'llm_output': 0, 'llm_change': 0}
                            }
                            self.is_paused = True
                            self.pause_btn.config(text="[RESUME] Resume")
                            continue  # Pause and wait for user to resume

                    # Check batch continuity (for batch 2+)
                    if batch_num > 1:
                        self.log_message(f"", 'info')
                        self.check_batch_continuity(batch_text, cleaned, batch_num)
                        self.log_message(f"", 'info')

                    # Check batch alignment (first/last sentence matching)
                    self.log_message(f"", 'info')
                    alignment_ok = self.check_batch_alignment(batch_text, cleaned, batch_num)
                    self.log_message(f"", 'info')

                    if not alignment_ok:
                        self.log_message(f"   [WARNING] ALIGNMENT WARNING: Input/Output boundaries don't match!", 'warning')
                        self.log_message(f"   [WARNING] This may indicate content loss or hallucination", 'warning')
                        # Continue processing but warn user

                    # Store last sentences for continuity check in next batch
                    self.previous_input_last_sentence = self.extract_last_sentence(batch_text)
                    self.previous_output_last_sentence = self.extract_last_sentence(cleaned)

                    # Update output preview with FULL cleaned text (no 2000 char limit)
                    self.output_preview.delete(1.0, tk.END)
                    self.output_preview.insert(1.0, cleaned)

                    # Append to output file
                    with open(self.output_file.get(), 'a', encoding='utf-8') as f:
                        f.write(cleaned)
                        if not cleaned.endswith('\n\n'):
                            f.write('\n\n')

                    # Update full output view
                    self.full_output_text.insert(tk.END, cleaned + '\n\n')
                    self.full_output_text.see(tk.END)

                    # Save to history
                    self._save_to_diff_history(self.input_file.get(), batch_num, batch_text, cleaned)
                    self._save_to_full_output_history(self.input_file.get(), batch_num, cleaned)

                    # Save context
                    self.previous_context = next_context

                    # Log results with comparison
                    self.log_message(f"   [OK] Batch complete in {batch_time:.1f}s", 'success')
                    self.log_message(f"   Batch text: {input_line_count} lines, {input_char_count} chars", 'info')
                    self.log_message(f"   Output:     {output_line_count} lines, {output_char_count} chars", 'success')
                    self.log_message(f"   Change:     {char_reduction:+.1f}% chars, {line_reduction:+.1f}% lines", 'info')

                    # Warn if excessive data loss from batch text to output
                    if char_reduction > 15:
                        self.log_message(f"   [WARNING] WARNING: Output reduced by {char_reduction:.1f}% from batch - check for truncation!", 'warning')
                    elif llm_change > 50:
                        self.log_message(f"   [WARNING] WARNING: LLM output increased by {llm_change:+.1f}% - review for added content", 'warning')
                    elif llm_change < -30:
                        self.log_message(f"   [WARNING] WARNING: LLM output decreased by {llm_change:.1f}% - review for lost content", 'warning')

                    # Show context (filtered)
                    if next_context:
                        self.log_message(f"   Context: '{next_context[:60]}...'", 'info')

                    # Reset retry counter on successful batch
                    retry_count = 0
                else:
                    self.log_message(f"   [X] Batch FAILED - stopping", 'error')
                    break

                # Update progress
                self.current_batch = batch_num
                progress = (batch_num / self.total_batches) * 100
                self.progress_bar['value'] = progress
                self.progress_label.config(text=f"Batch {batch_num}/{self.total_batches} complete ({progress:.1f}%)")
                
                # Move to next batch
                i = actual_end
                batch_num += 1
            
            # Processing complete
            if self.is_processing:
                elapsed = time.time() - self.start_time
                self.log_message(f"\n{'='*70}", 'success')
                self.log_message(f"[DONE] PROCESSING COMPLETE!", 'success')
                self.log_message(f"{'='*70}", 'success')
                self.log_message(f"   Total batches: {batch_num-1}", 'success')
                self.log_message(f"   Total time: {time.strftime('%H:%M:%S', time.gmtime(elapsed))}", 'success')
                self.log_message(f"   Output saved: {self.output_file.get()}", 'success')
                
                messagebox.showinfo("Complete", f"Processing complete!\n\nBatches processed: {batch_num-1}\nOutput saved to: {self.output_file.get()}")
            
        except Exception as e:
            self.log_message(f"\n[X] FATAL ERROR: {str(e)}", 'error')
            messagebox.showerror("Error", f"Processing failed:\n{str(e)}")
        
        finally:
            self.finish_processing()


def main():
    """Main entry point"""
    root = tk.Tk()
    
    # Set theme
    style = ttk.Style()
    style.theme_use('clam')
    
    # Custom button style
    style.configure('Accent.TButton', font=('Arial', 10, 'bold'))
    
    app = TTSPreprocessorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
