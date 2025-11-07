# Test Directory

This directory contains all active test files for the TTS Text Preprocessor project.

## Active Test Files

### test_multi_pass_processor.py
Test framework for the multi-pass OCR processor. Provides comprehensive deviation metrics comparing processed output against expected results.

**Key Features:**
- DeviationMetrics class with character/word/line similarity scoring
- OCRTestFramework for comparing processed vs expected output
- Overall scoring system (weighted: 30% char, 35% word, 25% line, 10% structure)
- Production readiness threshold: 85%

### test_integration.py
Integration test that runs the full multi-pass processor on INPUT.txt and compares against OUTPUT.txt.

**Usage:**
```bash
python test/test_integration.py
```

### test_gui_refactor.py
Tests the integration of multi_pass_processor into tts_preprocessor_gui.py.

**Usage:**
```bash
python test/test_gui_refactor.py
```

### analyze_differences.py
Detailed analysis tool that shows all character-level differences between PROCESSED_OUTPUT.txt and expected OUTPUT.txt.

**Usage:**
```bash
python test/analyze_differences.py
```

## Running Tests

All tests should be run from the repository root:

```bash
# Run integration test (requires docs/INPUT.txt and docs/OUTPUT.txt)
python test/test_integration.py

# Test GUI refactoring
python test/test_gui_refactor.py

# Analyze differences in detail
python test/analyze_differences.py
```

## Test Data

Test data files (INPUT.txt, OUTPUT.txt, etc.) are located in the `docs/` directory.
