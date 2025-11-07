#!/usr/bin/env python3
"""
Test framework for multi-pass OCR text processing.

Compares processing results against expected OUTPUT.txt and provides
detailed deviation metrics to establish production readiness.
"""

import difflib
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass
import re


@dataclass
class DeviationMetrics:
    """Metrics for comparing processed text against expected output."""

    # Overall metrics
    char_similarity: float  # 0-100%
    word_similarity: float  # 0-100%
    line_similarity: float  # 0-100%

    # Structural metrics
    paragraph_count_match: bool
    blank_line_count_match: bool
    line_count_ratio: float  # expected/actual

    # Content metrics
    apostrophe_fixes: int
    page_headers_removed: int
    word_fragments_fixed: int

    # Diff details
    missing_lines: List[str]
    extra_lines: List[str]
    different_lines: List[Tuple[str, str]]  # (expected, actual)

    # Overall score
    overall_score: float  # 0-100%

    def is_production_ready(self, threshold: float = 85.0) -> bool:
        """Determine if processing meets production threshold."""
        return self.overall_score >= threshold

    def get_report(self) -> str:
        """Generate detailed report of metrics."""
        report = []
        report.append("=" * 80)
        report.append("OCR PROCESSING TEST RESULTS")
        report.append("=" * 80)
        report.append("")

        # Overall Score
        status = "✅ PRODUCTION READY" if self.is_production_ready() else "❌ NEEDS IMPROVEMENT"
        report.append(f"Overall Score: {self.overall_score:.2f}% {status}")
        report.append("")

        # Similarity Metrics
        report.append("SIMILARITY METRICS:")
        report.append(f"  Character-level:  {self.char_similarity:.2f}%")
        report.append(f"  Word-level:       {self.word_similarity:.2f}%")
        report.append(f"  Line-level:       {self.line_similarity:.2f}%")
        report.append("")

        # Structural Metrics
        report.append("STRUCTURAL METRICS:")
        report.append(f"  Paragraph count:  {'✅ Match' if self.paragraph_count_match else '❌ Mismatch'}")
        report.append(f"  Blank lines:      {'✅ Match' if self.blank_line_count_match else '❌ Mismatch'}")
        report.append(f"  Line count ratio: {self.line_count_ratio:.2f}")
        report.append("")

        # Content Fixes
        report.append("CONTENT FIXES APPLIED:")
        report.append(f"  Apostrophes fixed:    {self.apostrophe_fixes}")
        report.append(f"  Page headers removed: {self.page_headers_removed}")
        report.append(f"  Word fragments fixed: {self.word_fragments_fixed}")
        report.append("")

        # Differences
        if self.missing_lines:
            report.append(f"MISSING LINES ({len(self.missing_lines)}):")
            for line in self.missing_lines[:5]:  # Show first 5
                report.append(f"  - {line[:70]}...")
            if len(self.missing_lines) > 5:
                report.append(f"  ... and {len(self.missing_lines) - 5} more")
            report.append("")

        if self.extra_lines:
            report.append(f"EXTRA LINES ({len(self.extra_lines)}):")
            for line in self.extra_lines[:5]:
                report.append(f"  + {line[:70]}...")
            if len(self.extra_lines) > 5:
                report.append(f"  ... and {len(self.extra_lines) - 5} more")
            report.append("")

        if self.different_lines:
            report.append(f"DIFFERENT LINES ({len(self.different_lines)}):")
            for expected, actual in self.different_lines[:3]:
                report.append(f"  Expected: {expected[:60]}...")
                report.append(f"  Actual:   {actual[:60]}...")
                report.append("")
            if len(self.different_lines) > 3:
                report.append(f"  ... and {len(self.different_lines) - 3} more differences")

        report.append("=" * 80)
        return "\n".join(report)


class OCRTestFramework:
    """Test framework for comparing OCR processing results."""

    def __init__(self, input_path: Path, expected_output_path: Path):
        """Initialize test framework with input and expected output files."""
        self.input_path = input_path
        self.expected_output_path = expected_output_path

        # Load files
        self.input_text = self.input_path.read_text(encoding='utf-8')
        self.expected_output = self.expected_output_path.read_text(encoding='utf-8')

    def compare_texts(self, actual_output: str) -> DeviationMetrics:
        """
        Compare actual output against expected output.

        Returns detailed deviation metrics.
        """
        # Character similarity
        char_similarity = self._calculate_similarity(
            self.expected_output,
            actual_output
        )

        # Word similarity
        expected_words = self.expected_output.split()
        actual_words = actual_output.split()
        word_similarity = self._calculate_similarity(
            ' '.join(expected_words),
            ' '.join(actual_words)
        )

        # Line similarity
        expected_lines = [l.strip() for l in self.expected_output.split('\n')]
        actual_lines = [l.strip() for l in actual_output.split('\n')]

        line_similarity = self._calculate_line_similarity(
            expected_lines,
            actual_lines
        )

        # Structural metrics
        expected_paragraphs = len([l for l in expected_lines if l])
        actual_paragraphs = len([l for l in actual_lines if l])
        paragraph_match = expected_paragraphs == actual_paragraphs

        expected_blank = self.expected_output.count('\n\n')
        actual_blank = actual_output.count('\n\n')
        blank_match = expected_blank == actual_blank

        line_count_ratio = len(actual_lines) / len(expected_lines) if expected_lines else 0

        # Content metrics
        apostrophe_fixes = self._count_apostrophe_fixes()
        page_headers_removed = self._count_page_headers()
        word_fragments_fixed = self._count_word_fragments()

        # Line diff details
        missing_lines, extra_lines, different_lines = self._get_line_diffs(
            expected_lines,
            actual_lines
        )

        # Calculate overall score
        overall_score = self._calculate_overall_score(
            char_similarity,
            word_similarity,
            line_similarity,
            paragraph_match,
            blank_match
        )

        return DeviationMetrics(
            char_similarity=char_similarity,
            word_similarity=word_similarity,
            line_similarity=line_similarity,
            paragraph_count_match=paragraph_match,
            blank_line_count_match=blank_match,
            line_count_ratio=line_count_ratio,
            apostrophe_fixes=apostrophe_fixes,
            page_headers_removed=page_headers_removed,
            word_fragments_fixed=word_fragments_fixed,
            missing_lines=missing_lines,
            extra_lines=extra_lines,
            different_lines=different_lines,
            overall_score=overall_score
        )

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity ratio between two texts (0-100%)."""
        ratio = difflib.SequenceMatcher(None, text1, text2).ratio()
        return ratio * 100

    def _calculate_line_similarity(self, lines1: List[str], lines2: List[str]) -> float:
        """Calculate line-by-line similarity."""
        matcher = difflib.SequenceMatcher(None, lines1, lines2)
        return matcher.ratio() * 100

    def _count_apostrophe_fixes(self) -> int:
        """Count number of apostrophe issues in input."""
        # Pattern: space + apostrophe + space (e.g., " ' ")
        pattern = r"\s'\s"
        return len(re.findall(pattern, self.input_text))

    def _count_page_headers(self) -> int:
        """Count number of page headers in input."""
        headers = 0
        header_patterns = [
            r'^The Ultimate Track \d+$',
            r'^THE TRACKER$',
            r'^Hie Utimate Track \d+$',
            r'^\d+ THE TRACKER$',
            r'^\d+ THETRACKER$',
        ]

        for line in self.input_text.split('\n'):
            line = line.strip()
            for pattern in header_patterns:
                if re.match(pattern, line):
                    headers += 1
                    break

        return headers

    def _count_word_fragments(self) -> int:
        """Count word fragments across lines."""
        fragments = 0
        lines = self.input_text.split('\n')

        for i in range(len(lines) - 1):
            current = lines[i].strip()
            next_line = lines[i + 1].strip()

            if not current or not next_line:
                continue

            # Check if current line ends mid-word and next starts with lowercase
            if current and not current[-1] in '.!?,;:' and next_line:
                # Check for patterns like "drop " + "ping"
                if current.split()[-1].islower() and next_line[0].islower():
                    # More sophisticated check for actual word break
                    last_word = current.split()[-1]
                    first_word = next_line.split()[0] if next_line.split() else ""
                    if len(last_word) <= 5 and len(first_word) <= 5:
                        fragments += 1

        return fragments

    def _get_line_diffs(
        self,
        expected: List[str],
        actual: List[str]
    ) -> Tuple[List[str], List[str], List[Tuple[str, str]]]:
        """Get detailed line differences."""
        matcher = difflib.SequenceMatcher(None, expected, actual)

        missing = []
        extra = []
        different = []

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'delete':
                missing.extend(expected[i1:i2])
            elif tag == 'insert':
                extra.extend(actual[j1:j2])
            elif tag == 'replace':
                for e, a in zip(expected[i1:i2], actual[j1:j2]):
                    different.append((e, a))

        return missing, extra, different

    def _calculate_overall_score(
        self,
        char_sim: float,
        word_sim: float,
        line_sim: float,
        para_match: bool,
        blank_match: bool
    ) -> float:
        """Calculate weighted overall score."""
        # Weights (total = 100%)
        weights = {
            'char': 0.30,
            'word': 0.35,
            'line': 0.25,
            'structure': 0.10
        }

        structure_score = 100 if (para_match and blank_match) else 50

        overall = (
            char_sim * weights['char'] +
            word_sim * weights['word'] +
            line_sim * weights['line'] +
            structure_score * weights['structure']
        )

        return overall


def run_test(processor_func, input_path: Path, expected_output_path: Path) -> DeviationMetrics:
    """
    Run test on a processor function.

    Args:
        processor_func: Function that takes input text and returns processed text
        input_path: Path to INPUT.txt
        expected_output_path: Path to OUTPUT.txt

    Returns:
        DeviationMetrics with results
    """
    # Initialize framework
    framework = OCRTestFramework(input_path, expected_output_path)

    # Process input
    processed_output = processor_func(framework.input_text)

    # Compare results
    metrics = framework.compare_texts(processed_output)

    return metrics


if __name__ == "__main__":
    # Example usage
    input_path = Path("/home/user/prep-text-for-tts/INPUT.txt")
    expected_output_path = Path("/home/user/prep-text-for-tts/OUTPUT.txt")

    # Dummy processor for testing the framework
    def dummy_processor(text: str) -> str:
        """Dummy processor that does nothing."""
        return text

    print("Testing framework with dummy processor...")
    metrics = run_test(dummy_processor, input_path, expected_output_path)
    print(metrics.get_report())
