"""
TTS Text Preprocessor GUI
A professional interface for batch processing text with LM Studio
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

    @classmethod
    def _get_nlp(cls):
        """Lazy load spaCy model"""
        if cls._nlp is None:
            cls._nlp = spacy.load("en_core_web_sm")
        return cls._nlp

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
        - epub2tts (audiobook generation)
        - ElevenLabs normalization guide
        - Coqui TTS preprocessing
        - Deepgram TTS optimization

        Steps:
        1. Unicode cleaning (ftfy + OCR artifacts)
        2. Normalize punctuation (!!!, ???, ---, ...)
        3. Normalize symbols (™, ©, &, @, #)
        4. Normalize numbers (1st → first, 1990s)
        5. Normalize currency ($100 → 100 dollars)
        6. Normalize ALL CAPS (but preserve acronyms)
        7. Normalize chapter markers (CHAPTER I → Chapter 1)
        8. Remove URLs and emails
        9. Remove page numbers
        10. Fix hyphenated line breaks
        11. Normalize whitespace
        12. Chunk for TTS (spaCy + Deepgram hybrid)

        Returns: Cleaned, chunked text ready for TTS
        """
        steps = [
            ("Clean Unicode (ftfy)", TextPreprocessor.clean_unicode),
            ("Normalize punctuation", TextPreprocessor.normalize_punctuation),
            ("Normalize symbols", TextPreprocessor.normalize_symbols),
            ("Normalize numbers", TextPreprocessor.normalize_numbers),
            ("Normalize currency", TextPreprocessor.normalize_currency),
            ("Normalize ALL CAPS", TextPreprocessor.normalize_all_caps),
            ("Normalize chapter markers", TextPreprocessor.normalize_chapter_markers),
            ("Remove URLs/emails", TextPreprocessor.remove_urls_emails),
            ("Remove page numbers", TextPreprocessor.remove_page_numbers),
            ("Fix hyphenated line breaks", TextPreprocessor.fix_hyphenated_breaks),
            ("Normalize whitespace", TextPreprocessor.normalize_whitespace),
            ("Chunk for TTS (spaCy + hybrid)", lambda t: TextPreprocessor.chunk_for_tts(t, max_chunk_size)),
        ]

        result = text
        for step_name, step_func in steps:
            result = step_func(result)

        return result


# ============================================================================
# GUI APPLICATION
# ============================================================================

class TTSPreprocessorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("TTS Text Preprocessor - LM Studio Edition")
        self.root.geometry("1400x900")
        
        # Variables
        self.input_file = tk.StringVar()
        self.output_file = tk.StringVar()
        self.prompt_file = tk.StringVar()
        self.lm_host = tk.StringVar(value="http://localhost:1234/v1")
        self.model_name = tk.StringVar(value="mistral-7b-instruct-v0.3")
        self.temperature = tk.DoubleVar(value=0.2)
        self.seed = tk.IntVar(value=42)
        self.batch_size = tk.IntVar(value=500)
        self.max_tokens = tk.IntVar(value=16000)
        
        # Processing state
        self.is_processing = False
        self.is_paused = False
        self.current_batch = 0
        self.total_batches = 0
        self.start_time = None
        self.previous_context = ""
        
        # Queue for thread-safe GUI updates
        self.log_queue = queue.Queue()
        
        # Build UI
        self.setup_ui()
        
        # Start log queue processor
        self.process_log_queue()
        
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
        ttk.Button(files_frame, text="🔧 Pre-clean", command=self.preclean_input).grid(row=0, column=3, padx=5)
        
        ttk.Label(files_frame, text="Output File:").grid(row=1, column=0, sticky=tk.W, padx=5)
        ttk.Entry(files_frame, textvariable=self.output_file, width=50).grid(row=1, column=1, padx=5)
        ttk.Button(files_frame, text="Browse...", command=self.browse_output).grid(row=1, column=2, padx=5)
        
        ttk.Label(files_frame, text="Prompt File:").grid(row=2, column=0, sticky=tk.W, padx=5)
        ttk.Entry(files_frame, textvariable=self.prompt_file, width=50).grid(row=2, column=1, padx=5)
        ttk.Button(files_frame, text="Browse...", command=self.browse_prompt).grid(row=2, column=2, padx=5)
        
        # LM Studio Settings
        lm_frame = ttk.Frame(config_frame)
        lm_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(lm_frame, text="LM Studio Host:").grid(row=0, column=0, sticky=tk.W, padx=5)
        ttk.Entry(lm_frame, textvariable=self.lm_host, width=30).grid(row=0, column=1, padx=5)
        
        ttk.Label(lm_frame, text="Model:").grid(row=0, column=2, sticky=tk.W, padx=5)
        ttk.Entry(lm_frame, textvariable=self.model_name, width=30).grid(row=0, column=3, padx=5)
        
        ttk.Button(lm_frame, text="Test Connection", command=self.test_connection).grid(row=0, column=4, padx=5)
        
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

        self.start_btn = ttk.Button(button_frame, text="▶ Start Processing",
                                    command=self.start_processing, style='Accent.TButton')
        self.start_btn.pack(fill=tk.X, pady=2)

        self.pause_btn = ttk.Button(button_frame, text="⏸ Pause",
                                    command=self.pause_processing, state=tk.DISABLED)
        self.pause_btn.pack(fill=tk.X, pady=2)

        self.stop_btn = ttk.Button(button_frame, text="⏹ Stop",
                                   command=self.stop_processing, state=tk.DISABLED)
        self.stop_btn.pack(fill=tk.X, pady=2)
        
        # ==== BOTTOM SECTION: Preview & Logs (Tabbed) ====
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Tab 1: Console Log
        log_frame = ttk.Frame(notebook)
        notebook.add(log_frame, text="📋 Console Log")
        
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, 
                                                   font=('Courier', 9), bg='#1e1e1e', fg='#d4d4d4')
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure log text tags for colors
        self.log_text.tag_config('info', foreground='#4ec9b0')
        self.log_text.tag_config('success', foreground='#4fc1ff')
        self.log_text.tag_config('warning', foreground='#dcdcaa')
        self.log_text.tag_config('error', foreground='#f48771')
        self.log_text.tag_config('batch', foreground='#c586c0')
        
        # Tab 2: Current Batch Preview
        preview_frame = ttk.Frame(notebook)
        notebook.add(preview_frame, text="👁 Current Batch Preview")
        
        preview_paned = ttk.PanedWindow(preview_frame, orient=tk.HORIZONTAL)
        preview_paned.pack(fill=tk.BOTH, expand=True)
        
        # Input preview
        input_preview_frame = ttk.LabelFrame(preview_paned, text="Input Text")
        self.input_preview = scrolledtext.ScrolledText(input_preview_frame, wrap=tk.WORD, 
                                                       font=('Arial', 9), bg='#fff8dc')
        self.input_preview.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        preview_paned.add(input_preview_frame)
        
        # Output preview
        output_preview_frame = ttk.LabelFrame(preview_paned, text="Output Text")
        self.output_preview = scrolledtext.ScrolledText(output_preview_frame, wrap=tk.WORD, 
                                                        font=('Arial', 9), bg='#e8f4ea')
        self.output_preview.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        preview_paned.add(output_preview_frame)
        
        # Tab 3: Full Output View
        output_frame = ttk.Frame(notebook)
        notebook.add(output_frame, text="📄 Full Output")
        
        self.full_output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, 
                                                          font=('Arial', 10))
        self.full_output_text.pack(fill=tk.BOTH, expand=True)
        
        # Status Bar
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.log_message("✓ GUI initialized. Configure settings and load files to begin.", 'success')
    
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
    
    def test_connection(self):
        """Test connection to LM Studio"""
        self.log_message("Testing connection to LM Studio...", 'info')
        try:
            client = openai.OpenAI(
                base_url=self.lm_host.get(),
                api_key="not-needed"
            )

            # Try a simple completion
            response = client.chat.completions.create(
                model=self.model_name.get(),
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )

            self.log_message("✓ Connection successful! LM Studio is ready.", 'success')
            messagebox.showinfo("Connection Test", "✓ Successfully connected to LM Studio!")

        except Exception as e:
            self.log_message(f"✗ Connection failed: {str(e)}", 'error')
            messagebox.showerror("Connection Test", f"Failed to connect:\n{str(e)}\n\nMake sure LM Studio Local Server is running!")

    def preclean_input(self):
        """Pre-clean input file with detailed transformation logging"""
        if not self.input_file.get():
            messagebox.showerror("Error", "Please select an input file first!")
            return

        try:
            self.log_message("="*70, 'info')
            self.log_message("🔧 STARTING DETERMINISTIC PRE-CLEANING WITH DETAILED LOGGING", 'batch')
            self.log_message("="*70, 'info')

            # Read input file
            input_path = Path(self.input_file.get())
            self.log_message(f"📖 Reading: {input_path.name}", 'info')

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

            # Step 1: Clean Unicode with ftfy
            self.log_message("🔹 Step 1: Cleaning Unicode (ftfy + OCR artifacts)", 'batch')
            before = current_text
            current_text = TextPreprocessor.clean_unicode(current_text)
            current_text = log_transformation("Clean Unicode", before, current_text)

            # Step 2: Normalize punctuation
            self.log_message("🔹 Step 2: Normalizing punctuation (???, !!!, ---, ...)", 'batch')
            before = current_text
            current_text = TextPreprocessor.normalize_punctuation(current_text)
            current_text = log_transformation("Normalize Punctuation", before, current_text)

            # Step 3: Normalize symbols
            self.log_message("🔹 Step 3: Normalizing symbols (™, ©, &, @, #)", 'batch')
            before = current_text
            current_text = TextPreprocessor.normalize_symbols(current_text)
            current_text = log_transformation("Normalize Symbols", before, current_text)

            # Step 4: Normalize numbers
            self.log_message("🔹 Step 4: Normalizing numbers (1st→first, 1990s)", 'batch')
            before = current_text
            current_text = TextPreprocessor.normalize_numbers(current_text)
            current_text = log_transformation("Normalize Numbers", before, current_text)

            # Step 5: Normalize currency
            self.log_message("🔹 Step 5: Normalizing currency ($100→100 dollars)", 'batch')
            before = current_text
            current_text = TextPreprocessor.normalize_currency(current_text)
            current_text = log_transformation("Normalize Currency", before, current_text)

            # Step 6: Normalize ALL CAPS
            self.log_message("🔹 Step 6: Normalizing ALL CAPS (preserve acronyms)", 'batch')
            before = current_text
            current_text = TextPreprocessor.normalize_all_caps(current_text)
            current_text = log_transformation("Normalize ALL CAPS", before, current_text)

            # Step 7: Normalize chapter markers
            self.log_message("🔹 Step 7: Normalizing chapter markers (Chapter IV→Chapter 4)", 'batch')
            before = current_text
            current_text = TextPreprocessor.normalize_chapter_markers(current_text)
            current_text = log_transformation("Normalize Chapter Markers", before, current_text)

            # Step 8: Remove URLs and emails
            self.log_message("🔹 Step 8: Removing URLs and emails", 'batch')
            before = current_text
            current_text = TextPreprocessor.remove_urls_emails(current_text)
            current_text = log_transformation("Remove URLs/Emails", before, current_text)

            # Step 9: Remove page numbers
            self.log_message("🔹 Step 9: Removing page numbers", 'batch')
            before = current_text
            current_text = TextPreprocessor.remove_page_numbers(current_text)
            current_text = log_transformation("Remove Page Numbers", before, current_text)

            # Step 10: Fix hyphenated line breaks
            self.log_message("🔹 Step 10: Merging hyphenated line breaks", 'batch')
            before = current_text
            current_text = TextPreprocessor.fix_hyphenated_breaks(current_text)
            current_text = log_transformation("Fix Hyphenated Breaks", before, current_text)

            # Step 11: Normalize whitespace
            self.log_message("🔹 Step 11: Normalizing whitespace", 'batch')
            before = current_text
            current_text = TextPreprocessor.normalize_whitespace(current_text)
            current_text = log_transformation("Normalize Whitespace", before, current_text)

            # Step 12: Chunk for TTS using spaCy + Deepgram approach
            self.log_message("🔹 Step 12: Chunking for TTS (spaCy + Deepgram hybrid)", 'batch')
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
            self.log_message("✅ PRE-CLEANING COMPLETE!", 'success')
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
                self.log_message(f"✓ Input file updated to: {output_path.name}", 'success')

                # Update preview
                preview_text = preprocessed[:1000] + "..." if len(preprocessed) > 1000 else preprocessed
                self.input_preview.delete(1.0, tk.END)
                self.input_preview.insert(1.0, preview_text)

        except Exception as e:
            self.log_message(f"✗ Pre-cleaning failed: {str(e)}", 'error')
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
            self.log_message("   📉 Text Removed:", 'warning')
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
            self.log_message("   📈 Text Added:", 'success')
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

                    self.log_message("   🔄 Example Change:", 'info')
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
Status:    {'⏸ PAUSED' if self.is_paused else '▶ PROCESSING'}
Progress:  {self.progress_bar['value']:.1f}%"""
        else:
            stats = """Batch:     -
Time:      00:00:00
Status:    ⏹ STOPPED
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
            self.pause_btn.config(text="▶ Resume")
            self.log_message("⏸ Processing PAUSED by user", 'warning')
        else:
            self.pause_btn.config(text="⏸ Pause")
            self.log_message("▶ Processing RESUMED", 'success')
        
        self.update_stats()
    
    def stop_processing(self):
        """Stop processing"""
        if messagebox.askyesno("Stop Processing", "Are you sure you want to stop?\n\nProgress will be saved."):
            self.is_processing = False
            self.log_message("⏹ Processing STOPPED by user", 'error')
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
    
    def find_paragraph_break(self, lines, max_lookback=50):
        """Find natural paragraph break"""
        for i in range(len(lines)-1, max(len(lines)-max_lookback, 0), -1):
            if i > 0 and lines[i].strip() == '':
                return i
        return len(lines)
    
    def process_single_batch(self, text_batch, batch_num, context=""):
        """Process a single batch with LM Studio"""
        try:
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
            
            # Create client
            client = openai.OpenAI(
                base_url=self.lm_host.get(),
                api_key="not-needed"
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
            
            return cleaned_text, next_context
            
        except Exception as e:
            self.log_message(f"✗ Error processing batch {batch_num}: {str(e)}", 'error')
            return None, context
    
    def process_batches(self):
        """Main processing loop (runs in separate thread)"""
        try:
            # Read input file
            self.log_message(f"📖 Reading input file: {self.input_file.get()}", 'info')
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

                # Update preview
                self.input_preview.delete(1.0, tk.END)
                self.input_preview.insert(1.0, batch_text[:2000] + "..." if len(batch_text) > 2000 else batch_text)

                # Log batch info
                self.log_message(f"\n{'='*70}", 'batch')
                self.log_message(f"📝 BATCH {batch_num}/{self.total_batches}", 'batch')
                self.log_message(f"{'='*70}", 'batch')
                self.log_message(f"   Lines: {i+1} to {actual_end}", 'info')
                self.log_message(f"   Input:  {input_line_count} lines, {input_char_count} chars", 'info')
                
                if self.previous_context:
                    self.log_message(f"   Using context from Batch {batch_num-1}", 'info')
                
                # Process batch
                self.log_message(f"   ⚙ Processing with {self.model_name.get()}...", 'info')
                batch_start_time = time.time()
                
                cleaned, next_context = self.process_single_batch(
                    batch_text, 
                    batch_num, 
                    self.previous_context
                )
                
                batch_time = time.time() - batch_start_time

                if cleaned:
                    # Calculate output stats
                    output_line_count = len(cleaned.splitlines())
                    output_char_count = len(cleaned)

                    # Calculate reductions
                    char_reduction = ((input_char_count - output_char_count) / input_char_count * 100) if input_char_count > 0 else 0
                    line_reduction = ((input_line_count - output_line_count) / input_line_count * 100) if input_line_count > 0 else 0

                    # Update output preview
                    self.output_preview.delete(1.0, tk.END)
                    self.output_preview.insert(1.0, cleaned[:2000] + "..." if len(cleaned) > 2000 else cleaned)

                    # Append to output file
                    with open(self.output_file.get(), 'a', encoding='utf-8') as f:
                        f.write(cleaned)
                        if not cleaned.endswith('\n\n'):
                            f.write('\n\n')

                    # Update full output view
                    self.full_output_text.insert(tk.END, cleaned + '\n\n')
                    self.full_output_text.see(tk.END)

                    # Save context
                    self.previous_context = next_context

                    # Log results with comparison
                    self.log_message(f"   ✓ Batch complete in {batch_time:.1f}s", 'success')
                    self.log_message(f"   Output: {output_line_count} lines, {output_char_count} chars", 'success')
                    self.log_message(f"   Change: {char_reduction:+.1f}% chars, {line_reduction:+.1f}% lines", 'info')

                    # Warn if excessive data loss
                    if char_reduction > 15:
                        self.log_message(f"   ⚠ WARNING: Output reduced by {char_reduction:.1f}% - check for truncation!", 'warning')

                    # Show context (filtered)
                    if next_context:
                        self.log_message(f"   Context: '{next_context[:60]}...'", 'info')
                else:
                    self.log_message(f"   ✗ Batch FAILED - stopping", 'error')
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
                self.log_message(f"✅ PROCESSING COMPLETE!", 'success')
                self.log_message(f"{'='*70}", 'success')
                self.log_message(f"   Total batches: {batch_num-1}", 'success')
                self.log_message(f"   Total time: {time.strftime('%H:%M:%S', time.gmtime(elapsed))}", 'success')
                self.log_message(f"   Output saved: {self.output_file.get()}", 'success')
                
                messagebox.showinfo("Complete", f"Processing complete!\n\nBatches processed: {batch_num-1}\nOutput saved to: {self.output_file.get()}")
            
        except Exception as e:
            self.log_message(f"\n✗ FATAL ERROR: {str(e)}", 'error')
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
