# Documentation Directory

This directory contains all documentation, specifications, and test data files.

## Documentation Files

### Project Documentation

**FINAL_SUMMARY.md**
- Complete project summary and implementation details
- Historical development overview

**GUI_USER_GUIDE.md**
- User guide for the TTS Text Preprocessor GUI
- Step-by-step usage instructions
- Feature explanations

**RTX_5080_LM_STUDIO_GUIDE.md**
- Guide for setting up LM Studio with RTX 5080
- Configuration and optimization tips

### Design & Planning Documents

**DUAL_MODE_UI_PLAN.md**
- Design document for dual-mode UI
- Feature planning and architecture

**OCR_MODEL_RESEARCH.md**
- Research notes on OCR models
- Model comparisons and recommendations

**ocr_text_processing_pseudologic.md**
- Specification for multi-pass OCR processing
- Pseudologic for 5-stage pipeline
- Recommended libraries and approaches

### Prompt Files

**IMPROVED_PROMPT_FINAL.txt**
- Final optimized prompt for LM Studio TTS processing

**PROMPT_FOR_PRECLEANED.txt**
- Prompt specifically for pre-cleaned text

**PROMPT_SIMPLIFIED.txt**
- Simplified version of the processing prompt

## Test Data Files

### Production Test Data

**INPUT.txt**
- Raw OCR input for testing (21,948 bytes)
- Contains all types of OCR errors: page headers, merged words, apostrophe spacing, etc.

**OUTPUT.txt**
- Expected clean output (21,205 bytes)
- Gold standard for testing (manually corrected)
- Used to establish 87.09% accuracy baseline

### Historical Test Data

**TEST_RACCOON.txt / TEST_RACCOON_FIXED.txt / TEST_RACCOON_FULL_FIXED.txt**
- Test data for raccoon encounter text
- Various stages of fixing

**TEST_COMPREHENSIVE.txt / TEST_COMPREHENSIVE_OUTPUT.txt**
- Comprehensive test scenarios

**TEST_INPUT.txt / TEST_OUTPUT.txt**
- Basic input/output test pairs

**TEST_USER_ISSUES.txt / TEST_USER_ISSUES_FIXED.txt**
- Real user-reported issues and fixes

## Usage

These files are referenced by test scripts in the `test/` directory and used for validating the multi-pass OCR processor's accuracy.

**Key Metrics:**
- INPUT.txt + OUTPUT.txt are the primary production test data
- Current processor achieves 87.09% overall accuracy
- Character-level: 99.75%
- Word-level: 92.75%
- Line-level: 78.82%
