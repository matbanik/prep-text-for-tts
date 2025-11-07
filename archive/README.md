# Archive Directory

This directory contains obsolete code files and tests that are no longer used in the active codebase but kept for reference.

## Archived Code Files

### ocr_gui.py
**Status:** Replaced by `tts_preprocessor_gui.py`

Old OCR GUI implementation. Superseded by the comprehensive TTS Text Preprocessor GUI which includes OCR processing plus TTS-specific normalization.

### ocr_processor.py
**Status:** Replaced by `multi_pass_processor.py`

Old OCR processor implementation. Superseded by the production-ready multi-pass processor that achieves 87.09% accuracy with a 5-stage pipeline.

## Archived Test Files

### CHECK_GUI_VERSION.py
Old script for checking GUI version. No longer needed.

### test_comprehensive.py
Old comprehensive test suite. Replaced by `test_multi_pass_processor.py` and `test_integration.py`.

### test_ocr.py
Old OCR-specific tests. Replaced by the new test framework.

### test_preprocessing.py / test_preprocessing_simple.py
Old preprocessing tests. Functionality now covered by the multi-pass processor tests.

### test_raccoon.py / test_raccoon_full.py
Old tests for raccoon text sample. The issues addressed by these tests are now handled by the multi-pass processor's deterministic cleaning stages.

### test_user_issues.py
Old test for user-reported issues. Issues now handled by the improved multi-pass processor.

## Why Archived?

These files represent previous iterations of the codebase that have been superseded by:

1. **Multi-Pass Processor (87.09% accuracy)**
   - Replaces: ocr_processor.py
   - 5-stage pipeline with comprehensive logging
   - Production-ready with ftfy + spacy integration

2. **TTS Preprocessor GUI (Refactored)**
   - Replaces: ocr_gui.py
   - Integrated multi-pass processor
   - Enhanced logging and statistics

3. **New Test Framework**
   - Replaces: All old test files
   - Quantitative metrics with weighted scoring
   - Character/word/line similarity analysis
   - Production readiness threshold (85%)

## Reference Only

These files are kept for historical reference and should not be used in new development. All active development should use:

- `tts_preprocessor_gui.py` (main GUI)
- `multi_pass_processor.py` (OCR processor)
- Tests in `test/` directory
