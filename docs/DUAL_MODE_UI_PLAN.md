# Dual-Mode UI Implementation Plan

## Overview
Restructure the GUI to support two distinct workflows:
1. **OCR Mode:** PDF → Image Extraction → OCR → Clean Text
2. **TTS Mode:** Text File → Pre-clean → LLM Processing → TTS-ready Output

## Architecture

### Tab Structure
```
┌─────────────────────────────────────────────────┐
│  TTS Text Preprocessor                          │
├─────────────────────────────────────────────────┤
│  [OCR Processing] [TTS Processing] <-- Tabs     │
├─────────────────────────────────────────────────┤
│                                                 │
│  Tab-specific content here                      │
│                                                 │
└─────────────────────────────────────────────────┘
```

## Tab 1: OCR Processing

### Configuration Section
```
┌─────────────────────────────────────────────────┐
│ OCR Configuration                               │
├─────────────────────────────────────────────────┤
│ Input PDF:  [Browse...] path/to/book.pdf       │
│ Output Text: [Browse...] path/to/output.txt    │
│                                                 │
│ OCR Model: [Qwen2-VL-2B (Recommended) ▼]       │
│   ℹ Fast, excellent accuracy, 90+ languages    │
│   Memory: ~8GB VRAM | Speed: Fast              │
│                                                 │
│ Options:                                        │
│   DPI: [300 ▼]  (Image quality)                │
│   [✓] Apply post-processing cleanup            │
│   [✓] Chunk for TTS (250 chars)                │
│                                                 │
│ [Check Dependencies] [Load OCR Model]          │
└─────────────────────────────────────────────────┘
```

### Model Selection Dropdown
- Qwen2-VL-2B (Recommended) ⭐
- Qwen2-VL-7B (Best Quality)
- GOT-OCR2.0 (Lightweight)
- MiniCPM-o-2.6 (Top Accuracy)

### Control Buttons
```
┌─────────────────────────────────────────────────┐
│ Controls                                        │
├─────────────────────────────────────────────────┤
│ [🔄 Load Model]        ← Load selected OCR     │
│ ────────────────────                            │
│ [▶ Start OCR]          ← Process PDF           │
│ [⏸ Pause]                                       │
│ [⏹ Stop]                                        │
└─────────────────────────────────────────────────┘
```

### Progress & Preview
```
┌─────────────────────────────────────────────────┐
│ Progress: ████████░░ 80% (Page 8/10)           │
│ Status: Processing page 8...                   │
│ Time: 00:02:15 | Est. remaining: 00:00:30      │
├─────────────────────────────────────────────────┤
│ Preview (Current Page):                         │
│ ┌─────────────────┬─────────────────┐           │
│ │ Original Image  │ Extracted Text  │           │
│ │                 │                 │           │
│ │ [Page preview]  │ The tracker...  │           │
│ │                 │                 │           │
│ └─────────────────┴─────────────────┘           │
└─────────────────────────────────────────────────┘
```

### Workflow
1. User selects PDF file
2. User selects OCR model
3. User clicks "Load Model" (downloads/loads into GPU)
4. User clicks "Start OCR"
5. System:
   - Converts PDF pages to images (PyMuPDF)
   - Processes each page with OCR model
   - (Optional) Applies TextPreprocessor cleanup
   - (Optional) Chunks for TTS
   - Saves to output file
6. Shows progress, preview, and statistics

## Tab 2: TTS Processing (Current Functionality)

### Configuration Section
```
┌─────────────────────────────────────────────────┐
│ TTS Preprocessing Configuration                │
├─────────────────────────────────────────────────┤
│ Input File:   [Browse...] path/to/text.txt     │
│ Output File:  [Browse...] path/to/output.txt   │
│ Prompt File:  [Browse...] prompt.txt           │
│                                                 │
│ LM Studio Settings:                             │
│   Host: [http://localhost:1234/v1]             │
│   Model: [mistral-7b-instruct-v0.3]            │
│   Temperature: [0.2] Seed: [42]                │
│   Batch Size: [500] Max Tokens: [16000]        │
│                                                 │
│ [Test Connection]                               │
└─────────────────────────────────────────────────┘
```

### Control Buttons
```
┌─────────────────────────────────────────────────┐
│ Controls                                        │
├─────────────────────────────────────────────────┤
│ [🔧 Pre-clean Input]   ← Deterministic cleanup │
│ ────────────────────                            │
│ [▶ Start Processing]   ← LLM batch processing  │
│ [⏸ Pause]                                       │
│ [⏹ Stop]                                        │
└─────────────────────────────────────────────────┘
```

### Progress & Preview
(Same as current implementation)

## Shared Components

### Console Log Tab
Both modes share the same console log output.

### Statistics Panel
Adapted to show relevant stats for each mode:

**OCR Mode:**
- Pages processed
- OCR time per page
- Total characters extracted
- Model memory usage

**TTS Mode:**
- Batches processed
- Tokens used
- Processing time
- Input/output comparison

## File Structure

```
tts_preprocessor_gui.py (modified)
├── OCRTab class
│   ├── setup_ui()
│   ├── load_ocr_model()
│   ├── start_ocr_processing()
│   └── process_pdf_thread()
│
├── TTSTab class
│   ├── setup_ui()
│   ├── preclean_input()
│   ├── start_processing()
│   └── process_batches()
│
└── MainWindow class
    ├── create_tab_interface()
    ├── shared_log_panel()
    └── shared_stats_panel()
```

## Dependencies to Add

```python
# requirements.txt additions
pymupdf>=1.23.0          # PDF processing
qwen-vl-utils            # For Qwen2-VL models
torch>=2.0.0
torchvision>=0.15.0
transformers>=4.37.0
accelerate>=0.28.0
tiktoken>=0.6.0          # For GOT-OCR
```

## Implementation Steps

### Phase 1: Restructure GUI ✓ (To Do)
1. Create tabbed interface
2. Move existing TTS UI to TTSTab class
3. Create empty OCRTab class

### Phase 2: OCR Tab UI ✓ (To Do)
1. Add PDF file selection
2. Add OCR model dropdown
3. Add dependency checker
4. Add model loader button
5. Add progress indicators

### Phase 3: OCR Integration ✓ (To Do)
1. Wire up OCRProcessor class
2. Implement PDF processing workflow
3. Add preview functionality
4. Integrate with TextPreprocessor for post-processing

### Phase 4: Polish
1. Add error handling
2. Add tooltips and help text
3. Test with sample PDFs
4. Performance optimization

## Benefits

1. **Unified Workflow:** One tool for OCR extraction AND TTS preparation
2. **Flexible:** Can use OCR alone, preprocessing alone, or both
3. **Efficient:** Direct pipeline: PDF → OCR → Cleanup → TTS chunks
4. **User-Friendly:** Clear separation of concerns, easy to understand

## Usage Example

### Full Pipeline (PDF → TTS):
1. **OCR Tab:** Load PDF, select Qwen2-VL-2B, enable "Apply post-processing cleanup" and "Chunk for TTS"
2. Click "Start OCR" → Get `OUTPUT_OCR.txt` (clean, chunked, TTS-ready)
3. Done! No LLM needed if OCR model does good job

### OCR + LLM Refinement:
1. **OCR Tab:** Process PDF with basic post-processing
2. **TTS Tab:** Load OCR output, use `PROMPT_FOR_PRECLEANED.txt`, refine with LLM
3. Get polished output

### Text-Only:
1. **TTS Tab:** Use existing workflow (what you have now)
