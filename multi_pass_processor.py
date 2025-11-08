#!/usr/bin/env python3
"""
Multi-Pass OCR Text Processor

Implements 5-stage processing pipeline:
1. Semantic Cleaning
2. Deterministic Cleaning
3. Sentence Reconstruction
4. Edge Case Collection
5. Edge Case Handling/Logging
"""

import re
from typing import List, Tuple, Dict, Set
from dataclasses import dataclass, field
from pathlib import Path
import logging
import ftfy
import spacy


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class EdgeCase:
    """Represents an edge case found during processing."""
    stage: str
    line_number: int
    issue_type: str
    original_text: str
    context: str
    confidence: str  # 'high', 'medium', 'low'


@dataclass
class ProcessingState:
    """Maintains state across processing stages."""
    text: str
    edge_cases: List[EdgeCase] = field(default_factory=list)
    stats: Dict[str, int] = field(default_factory=dict)

    def add_stat(self, key: str, increment: int = 1):
        """Add to statistics counter."""
        self.stats[key] = self.stats.get(key, 0) + increment

    def log_edge_case(self, stage: str, line_num: int, issue_type: str,
                      original: str, context: str, confidence: str):
        """Log an edge case."""
        self.edge_cases.append(EdgeCase(
            stage=stage,
            line_number=line_num,
            issue_type=issue_type,
            original_text=original,
            context=context,
            confidence=confidence
        ))


class MultiPassOCRProcessor:
    """
    Multi-pass OCR text processor implementing 5 stages.

    Based on pseudologic from ocr_text_processing_pseudologic.md
    """

    def __init__(self, enable_logging: bool = True):
        """Initialize processor."""
        self.enable_logging = enable_logging

        # Load spacy model for NLP tasks
        try:
            self.nlp = spacy.load("en_core_web_sm")
            # Disable unnecessary pipes for speed
            self.nlp.disable_pipes("ner", "lemmatizer")
        except OSError:
            logger.warning("Spacy model not found. Install with: python -m spacy download en_core_web_sm")
            self.nlp = None

        # Patterns for page headers (from pseudologic)
        self.header_patterns = [
            r'^The Ultimate Track \d+$',
            r'^THE TRACKER$',
            r'^Hie Utimate Track \d+$',  # OCR error variant
            r'^Hie Ultimate Track \d+$',  # Correct spelling variant
            r'^\d+ THE TRACKER$',
            r'^\d+ THETRACKER$',
        ]

    def process(self, text: str) -> Tuple[str, ProcessingState]:
        """
        Execute full 5-stage processing pipeline.

        Args:
            text: Raw OCR input text

        Returns:
            Tuple of (processed_text, processing_state)
        """
        state = ProcessingState(text=text)

        logger.info("="*80)
        logger.info("STARTING MULTI-PASS OCR PROCESSING")
        logger.info("="*80)

        # Stage 1: Semantic Cleaning
        logger.info("\n[STAGE 1] Semantic Cleaning...")
        state = self.stage1_semantic_cleaning(state)
        logger.info(f"  Removed {state.stats.get('headers_removed', 0)} page headers")
        logger.info(f"  Normalized whitespace: {state.stats.get('whitespace_normalized', 0)} changes")

        # Stage 2: Deterministic Cleaning
        logger.info("\n[STAGE 2] Deterministic Cleaning...")
        state = self.stage2_deterministic_cleaning(state)
        logger.info(f"  Fixed {state.stats.get('apostrophes_fixed', 0)} apostrophe issues")
        logger.info(f"  Fixed {state.stats.get('fragments_fixed', 0)} word fragments")

        # Stage 3: Sentence Reconstruction
        logger.info("\n[STAGE 3] Sentence Reconstruction...")
        state = self.stage3_sentence_reconstruction(state)
        logger.info(f"  Merged {state.stats.get('lines_merged', 0)} lines")
        logger.info(f"  Formed {state.stats.get('paragraphs_formed', 0)} paragraphs")

        # Stage 4: Edge Case Collection
        logger.info("\n[STAGE 4] Edge Case Collection...")
        state = self.stage4_edge_case_collection(state)
        logger.info(f"  Collected {len(state.edge_cases)} edge cases")

        # Stage 5: Edge Case Handling
        logger.info("\n[STAGE 5] Edge Case Handling...")
        state = self.stage5_edge_case_handling(state)
        logger.info(f"  Handled {state.stats.get('edge_cases_handled', 0)} edge cases")

        logger.info("\n" + "="*80)
        logger.info("PROCESSING COMPLETE")
        logger.info("="*80)

        return state.text, state

    # =========================================================================
    # STAGE 1: SEMANTIC CLEANING
    # =========================================================================

    def stage1_semantic_cleaning(self, state: ProcessingState) -> ProcessingState:
        """
        Stage 1: Remove page headers, normalize whitespace.

        Focuses on removing meaningless OCR artifacts.
        """
        text = state.text

        # Use ftfy to fix text encoding issues, mojibake, and Unicode problems
        text = ftfy.fix_text(text)
        logger.debug("  Applied ftfy text normalization")

        # Normalize line endings (handle CRLF, CR, LF)
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        lines = text.split('\n')
        cleaned_lines = []
        headers_removed = 0

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Check if line is a page header
            if self._is_page_header(stripped):
                headers_removed += 1
                logger.debug(f"  Line {i}: Removed header: {stripped[:50]}")
                continue

            cleaned_lines.append(line)

        # Join lines and normalize whitespace
        text = '\n'.join(cleaned_lines)

        # Normalize multiple blank lines to maximum 2
        while '\n\n\n' in text:
            text = text.replace('\n\n\n', '\n\n')
            state.add_stat('whitespace_normalized')

        state.text = text
        state.add_stat('headers_removed', headers_removed)
        return state

    def _is_page_header(self, line: str) -> bool:
        """Check if line matches page header patterns."""
        # Pattern matching
        for pattern in self.header_patterns:
            if re.match(pattern, line):
                return True

        # Heuristic: Short all-caps lines
        if len(line) < 30 and line.isupper() and len(line.split()) <= 3:
            return True

        # Heuristic: Just a page number
        if re.match(r'^\d+$', line) and len(line) <= 3:
            return True

        return False

    # =========================================================================
    # STAGE 2: DETERMINISTIC CLEANING
    # =========================================================================

    def stage2_deterministic_cleaning(self, state: ProcessingState) -> ProcessingState:
        """
        Stage 2: Fix apostrophes, hyphenated words, OCR-specific errors.

        Applies high-confidence deterministic transformations.
        """
        text = state.text

        # Fix OCR artifacts - Replace common OCR misreads
        # These are legitimate Unicode characters that OCR commonly mistakes
        ocr_artifacts = {
            '·': "'",   # Middle dot → apostrophe (common OCR error)
            '■': '',    # Box
            '●': '',    # Circle
            '∙': '',    # Bullet operator
            '•': '',    # Bullet
            '′': "'",   # Prime symbol → apostrophe
            '`': "'",   # Backtick → apostrophe (when used in contractions)
        }

        artifact_count = 0
        for artifact, replacement in ocr_artifacts.items():
            if artifact in text:
                count = text.count(artifact)
                text = text.replace(artifact, replacement)
                artifact_count += count
                logger.debug(f"  Replaced {count} instances of {repr(artifact)} with {repr(replacement)}")

        state.add_stat('ocr_artifacts_fixed', artifact_count)

        # Fix apostrophe spacing (e.g., "don ' t" -> "don't", "child ' s" -> "child's")
        # Handle both straight (') and curly/smart (', ') apostrophes
        original_text = text
        apostrophe_pattern = r"['\u2019\u2018]"  # Match ', ', or '

        # Count fixes before making changes
        apostrophe_fixes = len(re.findall(rf"\s+{apostrophe_pattern}", original_text))

        # Remove spaces before and after apostrophes
        text = re.sub(rf"\s+{apostrophe_pattern}\s+", "'", text)  # Space before and after
        text = re.sub(rf"\s+{apostrophe_pattern}", "'", text)      # Space only before

        state.add_stat('apostrophes_fixed', apostrophe_fixes)
        logger.debug(f"  Fixed {apostrophe_fixes} apostrophe spacing issues")

        # Fix quote spacing - ensure spaces inside quotes: "word" → " word "
        # Pattern: quote + non-space character → quote + space + character
        text = re.sub(r'"([^\s"])', r'" \1', text)  # Add space after opening quote
        text = re.sub(r'([^\s"])"', r'\1 "', text)  # Add space before closing quote

        # Fix word fragments across lines
        text, fragments_fixed = self._fix_word_fragments(text)
        state.add_stat('fragments_fixed', fragments_fixed)
        logger.debug(f"  Fixed {fragments_fixed} word fragments")

        # Fix common OCR errors
        text = self._fix_ocr_errors(text)

        state.text = text
        return state

    def _fix_word_fragments(self, text: str) -> Tuple[str, int]:
        """
        Fix word fragments split across lines - CONSERVATIVE approach.

        Only merge when there's explicit evidence of a word fragment:
        1. Line ends with trailing space + partial word (e.g., "drop ")
        2. Line ends with hyphen (e.g., "com-")
        3. Very short suffix pattern (e.g., "walk" + "ing" where ing <= 3 chars)

        Examples:
        - "drop \\nping" -> "dropping" (trailing space indicates fragment)
        - "com-\\npleted" -> "completed" (hyphen indicates fragment)
        - "dog\\nwith" -> "dog with" (NO merge - no evidence of fragment)
        """
        lines = text.split('\n')
        fixed_lines = []
        i = 0
        fragments_fixed = 0

        while i < len(lines):
            current = lines[i]

            # Look ahead to check for word fragments
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                current_stripped = current.strip()
                next_stripped = next_line.strip()

                # Skip if either line is empty
                if not current_stripped or not next_stripped:
                    fixed_lines.append(current)
                    i += 1
                    continue

                # Skip if current line ends with sentence-ending punctuation
                if current_stripped[-1] in '.!?':
                    fixed_lines.append(current)
                    i += 1
                    continue

                # Get last word of current line and first word of next line
                current_words = current_stripped.split()
                next_words = next_stripped.split()

                if not current_words or not next_words:
                    fixed_lines.append(current)
                    i += 1
                    continue

                last_word = current_words[-1]
                first_word = next_words[0]

                # Pattern 1: Line ends with hyphen (word break indicator)
                if last_word.endswith('-'):
                    merged_word = last_word[:-1] + first_word
                    current_words[-1] = merged_word
                    current_line_new = ' '.join(current_words)

                    if len(next_words) > 1:
                        lines[i + 1] = ' '.join(next_words[1:])
                        fixed_lines.append(current_line_new)
                        fragments_fixed += 1
                        i += 1
                        continue
                    else:
                        fixed_lines.append(current_line_new)
                        fragments_fixed += 1
                        i += 2
                        continue

                # Pattern 2: Current line has trailing space AND very short suffix pattern
                # (e.g., "drop " + "ping" where last_word <= 5 chars and first_word <= 4 chars)
                # Check for trailing space more explicitly
                has_trailing_space = len(current_stripped) < len(current.rstrip('\n\r'))
                if (has_trailing_space and
                    len(last_word) <= 5 and len(first_word) <= 4 and
                    last_word[-1].isalpha() and first_word[0].islower()):

                    merged_word = last_word + first_word
                    current_words[-1] = merged_word
                    current_line_new = ' '.join(current_words)

                    if len(next_words) > 1:
                        lines[i + 1] = ' '.join(next_words[1:])
                        fixed_lines.append(current_line_new)
                        fragments_fixed += 1
                        i += 1
                        continue
                    else:
                        fixed_lines.append(current_line_new)
                        fragments_fixed += 1
                        i += 2
                        continue

            fixed_lines.append(current)
            i += 1

        return '\n'.join(fixed_lines), fragments_fixed

    def _fix_ocr_errors(self, text: str) -> str:
        """Fix known OCR errors."""
        corrections = [
            ("Hie Utimate", "The Ultimate"),
            ("waking along", "walking along"),
            ("Juncoes", "Juncos"),  # Proper spelling
            ("Wolfs", "Wolf's"),  # Possessive
            ("Hfe", "Life"),  # OCR confusion: H + fe
        ]

        for error, correction in corrections:
            text = text.replace(error, correction)

        # Fix OCR confusion: 'll' being read as 'U' (capital U)
        # Examples: "stiU" → "still", "AU" → "All", "caU" → "call"
        # Pattern: letter + U + word boundary
        text = re.sub(r'(\w+)U\b', lambda m: m.group(1) + 'll', text)

        return text

    # =========================================================================
    # STAGE 3: SENTENCE RECONSTRUCTION
    # =========================================================================

    def stage3_sentence_reconstruction(self, state: ProcessingState) -> ProcessingState:
        """
        Stage 3: Merge lines into paragraphs.

        Groups lines into paragraphs (blank line = paragraph boundary),
        then merges lines within each paragraph into complete sentences.
        Preserves existing paragraph structure from INPUT.
        """
        text = state.text
        lines = text.split('\n')

        paragraph_buffer = ""
        output_lines = []
        lines_merged = 0

        for i, line in enumerate(lines):
            trimmed = line.strip()

            # Handle blank lines (potential paragraph boundaries)
            if not trimmed:
                # Only treat as paragraph boundary if buffer is complete or empty
                if paragraph_buffer:
                    # Check if buffer ends with terminal punctuation
                    if self._ends_with_terminal_punctuation(paragraph_buffer):
                        # Complete paragraph, output it
                        output_lines.append(paragraph_buffer)
                        paragraph_buffer = ""
                        # Add blank line for paragraph separation
                        if output_lines and output_lines[-1] != "":
                            output_lines.append("")
                    # else: incomplete sentence (e.g., ends with "The"),
                    # ignore blank line and continue building
                else:
                    # Empty buffer, add blank line if needed
                    if output_lines and output_lines[-1] != "":
                        output_lines.append("")
                continue

            # Build paragraph by merging lines
            if not paragraph_buffer:
                paragraph_buffer = trimmed
            else:
                # Add space before appending
                paragraph_buffer = paragraph_buffer + " " + trimmed
                lines_merged += 1

        # Handle remaining buffer
        if paragraph_buffer:
            output_lines.append(paragraph_buffer)

        # Count paragraphs (non-empty lines)
        paragraphs = len([l for l in output_lines if l.strip()])

        state.text = '\n'.join(output_lines)
        state.add_stat('lines_merged', lines_merged)
        state.add_stat('paragraphs_formed', paragraphs)
        return state

    def _ends_with_terminal_punctuation(self, line: str) -> bool:
        """Check if line ends with terminal punctuation."""
        if not line:
            return False

        # Check last non-whitespace character
        line = line.rstrip()
        if not line:
            return False

        last_char = line[-1]

        # Terminal punctuation
        if last_char in '.!?':
            return True

        # Check for quote after punctuation
        if len(line) >= 2 and line[-1] == '"' and line[-2] in '.!?':
            return True

        return False

    # =========================================================================
    # STAGE 4: EDGE CASE COLLECTION
    # =========================================================================

    def stage4_edge_case_collection(self, state: ProcessingState) -> ProcessingState:
        """
        Stage 4: Identify edge cases for review.

        Collects anomalies, low-confidence transformations, unusual patterns.
        """
        lines = state.text.split('\n')

        for i, line in enumerate(lines):
            stripped = line.strip()

            if not stripped:
                continue

            # Check for very short "sentences" (possible OCR error)
            if len(stripped) < 20 and stripped[-1] in '.!?':
                state.log_edge_case(
                    stage="Stage 4",
                    line_num=i,
                    issue_type="short_sentence",
                    original=stripped,
                    context=f"Line {i}",
                    confidence="medium"
                )

            # Check for sentences without ending punctuation
            if len(stripped) > 50 and not self._ends_with_terminal_punctuation(stripped):
                state.log_edge_case(
                    stage="Stage 4",
                    line_num=i,
                    issue_type="missing_punctuation",
                    original=stripped[:100],
                    context=f"Line {i}",
                    confidence="low"
                )

            # Check for suspicious character sequences
            if re.search(r'[a-z]{15,}', stripped):  # Very long words (possibly merged)
                matches = re.findall(r'[a-z]{15,}', stripped)
                for match in matches:
                    state.log_edge_case(
                        stage="Stage 4",
                        line_num=i,
                        issue_type="suspicious_long_word",
                        original=match,
                        context=stripped[:100],
                        confidence="medium"
                    )

        return state

    # =========================================================================
    # STAGE 5: EDGE CASE HANDLING
    # =========================================================================

    def stage5_edge_case_handling(self, state: ProcessingState) -> ProcessingState:
        """
        Stage 5: Handle or log edge cases for development.

        For now, this logs edge cases for manual review.
        Future: Could implement ML-based or dictionary-based resolution.
        """
        # Group edge cases by type
        by_type: Dict[str, List[EdgeCase]] = {}
        for ec in state.edge_cases:
            by_type.setdefault(ec.issue_type, []).append(ec)

        # Log summary
        if state.edge_cases:
            logger.info(f"\n  Edge Cases Summary:")
            for issue_type, cases in by_type.items():
                logger.info(f"    {issue_type}: {len(cases)} instances")

            # Could implement automatic handling here
            # For now, just count as "handled" (logged)
            state.add_stat('edge_cases_handled', len(state.edge_cases))

        return state


def process_file(input_path: Path, output_path: Path = None) -> ProcessingState:
    """
    Process an OCR text file through all 5 stages.

    Args:
        input_path: Path to input OCR text
        output_path: Optional path to save output

    Returns:
        ProcessingState with results
    """
    # Read input
    input_text = input_path.read_text(encoding='utf-8')

    # Process
    processor = MultiPassOCRProcessor()
    processed_text, state = processor.process(input_text)

    # Save output
    if output_path:
        output_path.write_text(processed_text, encoding='utf-8')
        logger.info(f"\nOutput saved to: {output_path}")

    return state


if __name__ == "__main__":
    # Test with INPUT.txt
    input_path = Path("/home/user/prep-text-for-tts/INPUT.txt")
    output_path = Path("/home/user/prep-text-for-tts/PROCESSED_OUTPUT.txt")

    print("\nProcessing INPUT.txt...")
    state = process_file(input_path, output_path)

    print("\nProcessing Statistics:")
    for key, value in state.stats.items():
        print(f"  {key}: {value}")
