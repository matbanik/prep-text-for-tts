# TTS Text Preprocessor

A professional GUI application for batch processing text with Qwen API (Alibaba Cloud Model Studio) to prepare content for high-quality text-to-speech conversion.

## Features

### 🔐 Security
- **Encrypted API Key Storage**: API keys encrypted at rest using Fernet symmetric encryption
- **Machine-Specific Encryption**: Encryption key derived from machine identifier
- **API Key Masking**: All logs mask API keys (shows only first 4 + last 4 characters)
- **Auto .gitignore**: Settings file automatically excluded from version control

### 🌐 Qwen API Integration
- Support for both **Singapore** and **Beijing** regions
- Multiple model options including free tier models:
  - `qwen-flash` - Most economical (recommended for free tier)
  - `qwen-plus` - Balanced performance
  - `qwen-max` - Most powerful
  - `qwen-coder` - Code-optimized
  - `qwq-plus` - Reasoning model
- OpenAI-compatible API interface
- Connection testing before processing

### 🎯 AI-Powered Text Processing
- **Context-Aware Transformations**:
  - Homograph disambiguation (lead[leed] vs lead[led])
  - Semantic number formatting (2024 → "twenty twenty-four")
  - Context-aware abbreviations (Dr. = Doctor vs Drive)
  - Sentence boundaries and punctuation
  - Prosodic markers for natural speech
  - Dialogue structure tracking

### 🔍 Quality Validation
- **LLM I/O Validation**:
  - Compares characters sent vs received from LLM
  - Stops processing if output >2x input (hallucination detection)
  - Stops processing if output <50% input (truncation detection)
  - Warns on suspicious size changes

- **Batch Alignment Detection**:
  - Compares first/last sentences between INPUT and OUTPUT
  - Fuzzy matching (70% threshold) allows minor transformations
  - Shows word-level diffs when misalignment detected
  - Character-level similarity scoring

- **Batch Continuity Checking**:
  - Verifies smooth transitions between consecutive batches
  - Compares batch N-1 OUTPUT last sentence vs batch N OUTPUT first sentence
  - Detects duplicate content, gaps, or overlaps at boundaries
  - Validates narrative flow consistency

### 🛠️ Pre-processing Tools
- **Multi-Pass OCR Cleaning** (87.09% accuracy):
  - Fix merged words and spacing issues
  - Remove page numbers and headers
  - Normalize contractions and apostrophes
  - Fix hyphenated line breaks
  - Symbol and currency normalization
  - ALL CAPS normalization
  - Chapter marker standardization

### 💾 Settings Management
- Persistent settings stored in `settings.json`
- Auto-save on window close and field changes
- Remembers last used files
- Region and model preferences
- Processing parameters (temperature, seed, batch size, max tokens)

### 📊 Real-Time Monitoring
- Live progress tracking with progress bar
- Detailed batch-by-batch logging with color coding
- Statistics display (batches processed, elapsed time)
- Input/output preview panels
- Full output view tab

## Installation

### Prerequisites
- Python 3.8 or higher
- Qwen API key from [Alibaba Cloud Model Studio](https://modelstudio.console.alibabacloud.com)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/matbanik/prep-text-for-tts.git
cd prep-text-for-tts
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. (Optional) Download spaCy model for enhanced text processing:
```bash
python -m spacy download en_core_web_sm
```

## Qwen API Setup

### Getting Your API Key

1. Visit [Alibaba Cloud Model Studio](https://modelstudio.console.alibabacloud.com)
2. Create an account or sign in
3. Navigate to **Key Management** in the console
4. Create a new API key
5. Copy the key (you'll enter it in the application)

### Free Tier Information

**Available in Singapore region only** (not Beijing):
- Each model has **1 million tokens** free quota
- Valid for **90 days** from activation
- All free tier models listed in the app

**Recommended Free Tier Models:**
- `qwen-flash` - Most economical, best for starting out
- `qwen-plus` - Better quality if you need it
- `qwen-max-latest` - Separate quota from qwen-max

**Check Your Quota:**
Visit the [Model Studio Console](https://modelstudio.console.alibabacloud.com) to view remaining tokens for each model.

## Usage

### Starting the Application

```bash
python tts_preprocessor_gui.py
```

### First-Time Setup

1. **Enter API Key**:
   - Paste your Qwen API key in the "API Key" field
   - Click the 👁 button to show/hide key
   - Key is automatically encrypted when you click away from the field

2. **Select Region**:
   - Choose **"singapore"** for free tier access
   - Choose **"beijing"** if you're using that region

3. **Select Model**:
   - Start with **"qwen-flash"** (most economical)
   - Try other models if needed

4. **Test Connection**:
   - Click "Test Connection" to verify your setup
   - Should see "✓ Successfully connected to Qwen API!"

### Processing Text

1. **Select Input File**: Browse to your text file (e.g., OCR output)

2. **Select Output File**: Choose where to save processed text

3. **Select Prompt File**: Choose the TTS prompt (use `TTS_PROMPT_V2.txt`)

4. **(Optional) Pre-clean**: Click "🔧 Pre-clean" to run deterministic OCR cleanup first

5. **Configure Parameters**:
   - **Temperature**: 0.2 (recommended for consistent output)
   - **Seed**: 42 (for reproducibility)
   - **Batch Size**: 500 lines per batch
   - **Max Tokens**: 16000 (adjust based on model limits)

6. **Start Processing**: Click "▶ Start Processing"

7. **Monitor Progress**:
   - Watch the progress bar and batch logs
   - Check the "Current Batch Preview" tab for real-time comparison
   - Review alignment and continuity checks in the logs

8. **Review Output**:
   - Check "Full Output" tab for complete processed text
   - Review logs for any warnings or alignment issues
   - Output saved to your selected file

### Understanding the Logs

**Batch Processing Logs:**
```
======================================================================
📝 BATCH 1/10
======================================================================
   Lines: 1 to 487
   Input:  487 lines, 23456 chars
   Using context from Batch 0
   ⚙ Processing with qwen-flash...
   📤 Sent to LLM:      23456 chars
   📥 Received from LLM: 22134 chars (-5.6%)
```

**Alignment Check:**
```
   ==================================================================
   🔍 BATCH ALIGNMENT CHECK
   ==================================================================
   📥 INPUT First sentence:
      'The tracker examined the footprints carefully.'
   📤 OUTPUT First sentence:
      'The tracker examined the footprints carefully.'
   ✓ First sentences aligned

   📥 INPUT Last sentence:
      'He knew the animal was nearby.'
   📤 OUTPUT Last sentence:
      'He knew the animal was nearby.'
   ✓ Last sentences aligned
   ==================================================================
```

**Continuity Check (Batch 2+):**
```
   ==================================================================
   🔗 BATCH CONTINUITY CHECK (Batch 1 → 2)
   ==================================================================
   📤 Generated Output Continuity:
      BATCH 1 OUTPUT last sentence:
      'He knew the animal was nearby.'
      BATCH 2 OUTPUT first sentence:
      'The next morning, he continued tracking.'
      ✓ Output flows naturally between batches
   ==================================================================
```

**Warning Examples:**
```
   ⚠ WARNING: First sentences DO NOT match!
   🔄 OUTPUT diff view (FIRST sentence):
      ➖ Removed: carefully, examined
      ➕ Added: looked, studied
      📊 Similarity: 65.2%
```

## Project Structure

```
prep-text-for-tts/
├── tts_preprocessor_gui.py      # Main GUI application
├── multi_pass_processor.py      # OCR cleaning module
├── TTS_PROMPT_V2.txt             # AI-optimized TTS prompt (focused on semantic tasks)
├── IMPROVED_PROMPT_FINAL.txt    # Legacy prompt (includes mechanical cleanup)
├── requirements.txt              # Python dependencies
├── settings.json                 # User settings (encrypted API key) - auto-generated
└── README.md                     # This file
```

## Security Best Practices

1. **Never commit `settings.json`**: Already in `.gitignore`
2. **API Key Protection**: Keys encrypted at rest, masked in logs
3. **Review Logs**: Check logs before sharing to ensure no sensitive data
4. **Regional Keys**: Singapore and Beijing API keys are different - use the correct one

## Troubleshooting

### "Free tier exhausted" Error
- You've used all 1M tokens for that specific model
- Try a different model (each has separate quota)
- Check quota at [Model Studio Console](https://modelstudio.console.alibabacloud.com)
- Wait for 90-day quota reset

### Connection Failed
- Verify API key is correct
- Ensure region matches your API key (Singapore vs Beijing)
- Check internet connection
- Verify Alibaba Cloud service status

### Alignment Warnings
- Review the specific sentences flagged
- Check if LLM is adding/removing content
- Adjust prompt if necessary
- May indicate model limitations - try a different model

### Output Size Errors
- "Output >2x input" = LLM hallucinating content
- "Output <50% input" = LLM truncating content
- Try adjusting `max_tokens` setting
- Try a different model
- Reduce batch size

## Advanced Configuration

### Custom Prompts
Edit `TTS_PROMPT_V2.txt` to customize LLM behavior. Current prompt focuses on:
- Homograph disambiguation
- Context-aware number/date formatting
- Context-aware abbreviation expansion
- Sentence boundaries & punctuation
- Prosodic markers
- Dialogue structure

### Batch Size Tuning
- Smaller batches (100-300 lines): Better accuracy, slower processing
- Larger batches (500-1000 lines): Faster processing, may lose context
- Default 500 lines is recommended for most content

### Temperature Settings
- 0.0-0.3: More consistent, deterministic output
- 0.4-0.7: More creative, varied output
- 0.8-1.0: Highly creative, less predictable

## Development

### Requirements
- Python 3.8+
- tkinter (usually included with Python)
- openai >= 1.0.0
- cryptography >= 41.0.0
- ftfy >= 6.1.0
- spacy >= 3.7.0

### Contributing
Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is provided as-is for text preprocessing purposes.

## Acknowledgments

- **Qwen AI** by Alibaba Cloud for the language models
- **OpenAI** for the compatible API interface
- **spaCy** for NLP utilities
- **cryptography** library for secure key storage

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the logs for specific error messages
3. Open an issue on GitHub with:
   - Error message (with API key masked)
   - Steps to reproduce
   - Model and settings used

---

**Note**: This tool uses AI language models which may produce unexpected results. Always review the output before using it for production TTS systems.
