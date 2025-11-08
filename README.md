# TTS Text Preprocessor

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A professional text preprocessing application for converting OCR output into clean, TTS-ready text. Features a production-ready multi-pass OCR processor achieving **87.09% accuracy** and comprehensive TTS normalization.

*Professional interface with real-time processing and detailed transformation logging*

## ✨ Features

### 🎯 Production-Ready OCR Processing (87.09% Accuracy)
- **5-Stage Multi-Pass Pipeline**:
  - Stage 1: Semantic Cleaning (ftfy, page headers, whitespace)
  - Stage 2: Deterministic Cleaning (apostrophes, word fragments, OCR errors)
  - Stage 3: Sentence Reconstruction (paragraph merging)
  - Stage 4: Edge Case Collection
  - Stage 5: Edge Case Handling
- **Comprehensive Statistics**: Detailed logging of all transformations
- **Edge Case Tracking**: Collects anomalies for continuous improvement

![Screenshot](./TTS.jpg)
![Screenshot](./TTS2.jpg)

### 🎤 TTS-Specific Normalization
- Punctuation normalization (!!!, ???, ---, ...)
- Symbol conversion (™, ©, &, @, #)
- Number expansion (1st → first, 1990s)
- Currency formatting ($100 → 100 dollars)
- ALL CAPS normalization (preserve acronyms)
- Chapter marker standardization
- URL and email removal
- Smart text chunking (spaCy + Deepgram hybrid approach)

### 🖥️ Professional GUI
- Real-time processing with progress tracking
- Detailed transformation logging with before/after examples
- File-based batch processing
- Integration with LM Studio for AI-powered refinement
- Pause/resume/stop controls
- Statistics dashboard

## 🚀 Quick Start

### Windows

Simply run the included launcher script:

```powershell
.\run.ps1
```

### Linux / macOS

Simply run the included launcher script:

```bash
./run.sh
```

The script will automatically:
- ✓ Check for Python installation
- ✓ Verify pip is available
- ✓ Install required packages (openai, ftfy, spacy)
- ✓ Download spaCy language model
- ✓ Launch the GUI application

### Manual Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/prep-text-for-tts.git
   cd prep-text-for-tts
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

3. **Launch the application**:
   ```bash
   python tts_preprocessor_gui.py
   ```

## 📋 Requirements

- **Python**: 3.8 or higher
- **Operating System**: Windows, macOS, or Linux
- **Dependencies**:
  - `openai>=1.0.0` (for LM Studio integration)
  - `ftfy>=6.0.0` (for Unicode/mojibake fixing)
  - `spacy>=3.0.0` (for NLP and sentence segmentation)
  - `tkinter` (usually included with Python)

## 📖 Usage

### Basic Workflow

1. **Select Input File**: Choose your OCR text file (.txt)
2. **Pre-Clean Text**: Click "Pre-Clean Input" to run the multi-pass OCR processor
3. **Review Statistics**: Check transformation details in the log window
4. **Optional AI Refinement**: Configure LM Studio endpoint and process with AI
5. **Save Output**: Pre-cleaned file is automatically saved with `_precleaned` suffix

### Processing Pipeline

```
Raw OCR Text
    ↓
[Multi-Pass OCR Processor - 87.09% Accuracy]
    ├─ Stage 1: Semantic Cleaning
    ├─ Stage 2: Deterministic Cleaning
    ├─ Stage 3: Sentence Reconstruction
    ├─ Stage 4: Edge Case Collection
    └─ Stage 5: Edge Case Handling
    ↓
[TTS Normalization - 10 Steps]
    ├─ Punctuation normalization
    ├─ Symbol conversion
    ├─ Number expansion
    ├─ Currency formatting
    ├─ ALL CAPS normalization
    ├─ Chapter markers
    ├─ URL/email removal
    ├─ Page number removal
    ├─ Whitespace normalization
    └─ Smart chunking for TTS
    ↓
Clean TTS-Ready Text
```

## 🏗️ Architecture

### Project Structure

```
prep-text-for-tts/
├── tts_preprocessor_gui.py      # Main GUI application
├── multi_pass_processor.py      # OCR processor (87.09% accuracy)
├── run.ps1                       # Windows launcher script
├── run.sh                        # Linux/macOS launcher script
├── requirements.txt              # Python dependencies
├── requirements_ocr.txt          # Optional OCR model dependencies
│
├── test/                         # Test suite
│   ├── test_multi_pass_processor.py
│   ├── test_integration.py
│   ├── test_gui_refactor.py
│   └── analyze_differences.py
│
├── docs/                         # Documentation & test data
│   ├── GUI_USER_GUIDE.md
│   ├── ocr_text_processing_pseudologic.md
│   └── INPUT.txt / OUTPUT.txt (test data)
│
└── archive/                      # Historical code (reference only)
```

### Multi-Pass OCR Processor

The `MultiPassOCRProcessor` class implements a 5-stage pipeline:

```python
from multi_pass_processor import MultiPassOCRProcessor

processor = MultiPassOCRProcessor()
cleaned_text, state = processor.process(raw_ocr_text)

# Access statistics
print(f"Headers removed: {state.stats['headers_removed']}")
print(f"Apostrophes fixed: {state.stats['apostrophes_fixed']}")
print(f"Lines merged: {state.stats['lines_merged']}")
print(f"Edge cases: {len(state.edge_cases)}")
```

**Key Metrics** (tested on production OCR data):
- Overall Accuracy: **87.09%**
- Character-level: **99.75%**
- Word-level: **92.75%**
- Line-level: **78.82%**

## 🧪 Testing

Run the test suite:

```bash
# Test multi-pass processor
python test/test_integration.py

# Test GUI integration
python test/test_gui_refactor.py

# Analyze differences in detail
python test/analyze_differences.py
```

## 📊 Performance

The multi-pass processor has been extensively tested on real OCR output:

| Metric | Score | Details |
|--------|-------|---------|
| **Overall Accuracy** | 87.09% | Production-ready (exceeds 85% threshold) |
| **Character-level** | 99.75% | Near-perfect character accuracy |
| **Word-level** | 92.75% | Excellent word preservation |
| **Line-level** | 78.82% | Good structural accuracy |

**Processing Speed**: ~1000 lines/second on modern hardware

## 🔧 Configuration

### LM Studio Integration

1. Install and run [LM Studio](https://lmstudio.ai/)
2. Load a text generation model
3. Start the local server (default: http://localhost:1234)
4. In the GUI:
   - Enter server URL
   - Click "Test Connection"
   - Configure batch settings
   - Process with AI refinement

### Customization

Edit `multi_pass_processor.py` to customize:
- Page header patterns
- OCR error corrections
- Word fragment detection rules
- Edge case detection thresholds

## 📚 Documentation

- [GUI User Guide](docs/GUI_USER_GUIDE.md) - Detailed usage instructions
- [OCR Processing Specification](docs/ocr_text_processing_pseudologic.md) - Technical specification
- [LM Studio Setup Guide](docs/RTX_5080_LM_STUDIO_GUIDE.md) - GPU optimization guide
- [Test Framework](test/README.md) - Test documentation

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 🐛 Bug Reports

Found a bug? Please open an issue with:
- Python version
- Operating system
- Sample input text (if applicable)
- Expected vs actual behavior
- Error messages/logs

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **ftfy** - Text fixing library by Robyn Speer
- **spaCy** - Industrial-strength NLP by Explosion AI
- **epub2tts** - Audiobook generation inspiration
- **Deepgram** - TTS optimization best practices
- **LM Studio** - Local LLM inference platform

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

<div align="center">

**[⬆ Back to Top](#tts-text-preprocessor)**

Made with ❤️ for the TTS community

</div>
