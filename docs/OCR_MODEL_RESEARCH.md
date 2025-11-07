# OCR Model Research for TTS-Friendly Text Extraction

## Use Case
Extract clean text from book PDFs (scanned images) for Text-to-Speech processing.

## Top Recommended Models (2025)

### 1. Qwen2-VL (RECOMMENDED) ⭐

**Model Variants:**
- `Qwen/Qwen2-VL-2B-Instruct` (fast, good quality)
- `Qwen/Qwen2-VL-7B-Instruct` (better quality)
- `Qwen/Qwen2-VL-72B-Instruct` (maximum quality, requires powerful GPU)

**Performance:**
- **OCRBench:** 845
- **DocVQA:** 94.5%
- **TextVQA:** 84.3%
- **Languages:** 90+ supported

**Strengths:**
- Excellent balance of speed and accuracy
- Strong document understanding
- Handles structured layouts well
- 63 quantization variants available
- Active community support

**Requirements:**
```bash
pip install git+https://github.com/huggingface/transformers
pip install qwen-vl-utils
```

**Usage:**
```python
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info

model = Qwen2VLForConditionalGeneration.from_pretrained("Qwen/Qwen2-VL-2B-Instruct")
processor = AutoProcessor.from_pretrained("Qwen/Qwen2-VL-2B-Instruct")

messages = [{
    "role": "user",
    "content": [
        {"type": "image", "image": "path/to/page.jpg"},
        {"type": "text", "text": "Extract all text from this page."}
    ]
}]

# Process and generate
```

**Why for TTS:**
- Clean text output
- Good at preserving paragraph structure
- Handles various fonts and layouts
- Minimal post-processing needed

---

### 2. GOT-OCR2.0 (LIGHTWEIGHT ALTERNATIVE)

**Model:**
- `ucaslcl/GOT-OCR2_0` (580M parameters)

**Performance:**
- Specialized end-to-end OCR model
- Fast inference (smaller model)
- Multiple output formats (plain text, markdown, HTML)

**Strengths:**
- Lightweight (only 580M params)
- OCR-specific design
- Fine-grained control (bounding boxes, regions)
- Multi-crop mode for large documents
- 58K+ monthly downloads

**Requirements:**
```bash
pip install torch==2.0.1 torchvision==0.15.2
pip install transformers==4.37.2
pip install tiktoken verovio accelerate
```

**Usage:**
```python
from transformers import AutoModel, AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained('ucaslcl/GOT-OCR2_0', trust_remote_code=True)
model = AutoModel.from_pretrained('ucaslcl/GOT-OCR2_0', trust_remote_code=True)

# Basic OCR
result = model.chat(tokenizer, image_path, ocr_type='ocr')

# Formatted text with structure
result = model.chat(tokenizer, image_path, ocr_type='format')
```

**Why for TTS:**
- Fast processing
- Can output formatted text (preserves paragraphs)
- Good for batch processing
- Lower memory requirements

---

### 3. MiniCPM-o-2.6 (HIGHEST ACCURACY)

**Model:**
- `openbmb/MiniCPM-o-2_6` (8B parameters)

**Performance:**
- **OCRBench:** #1 on leaderboard
- Beats GPT-4o, GPT-4V, Gemini 1.5 Pro
- Handles up to 1.8 million pixel images

**Strengths:**
- Best-in-class accuracy
- Efficient token usage (640 tokens for 1.8MP image)
- Handles any aspect ratio
- Good for high-resolution scans

**Why for TTS:**
- Highest accuracy means fewer OCR errors
- Better at complex layouts
- Good for challenging scans

---

## Comparison vs LightOnOCR-1B-1025

| Feature | LightOnOCR-1B | Qwen2-VL-2B | GOT-OCR2.0 | MiniCPM-o-2.6 |
|---------|---------------|-------------|------------|---------------|
| **Size** | 1B | 2B | 580M | 8B |
| **OCRBench** | Unknown | 845 | Good | #1 |
| **DocVQA** | Unknown | 94.5% | Good | Excellent |
| **Languages** | Limited | 90+ | Multi | Multi |
| **Speed** | Fast | Fast | Very Fast | Medium |
| **Structure** | Basic | Excellent | Good | Excellent |
| **Community** | Small | Large | Active | Growing |

## Recommendation for Your Use Case

**For book PDFs → TTS text:**

**Primary Choice: Qwen2-VL-2B-Instruct**
- Best balance of speed, accuracy, and ease of use
- Excellent document understanding
- Clean text output
- Well-supported

**Fallback: GOT-OCR2.0**
- If you need faster processing
- If you have limited GPU memory
- If you want lightweight deployment

**Maximum Quality: MiniCPM-o-2.6**
- If accuracy is paramount
- If you have powerful GPU
- If you have challenging/low-quality scans

## Integration Approach

1. **PDF → Images:** Use `pdf2image` or `PyMuPDF` to extract pages
2. **OCR Processing:** Use one of the models above
3. **Post-processing:** Apply your existing `TextPreprocessor` for cleanup
4. **Chunking:** Use your existing TTS chunking (250 chars)

## Installation Plan

```bash
# Core dependencies
pip install transformers accelerate torch torchvision
pip install pdf2image pillow

# For Qwen2-VL
pip install qwen-vl-utils

# For GOT-OCR
pip install tiktoken verovio

# For PDF handling
pip install PyMuPDF  # or pymupdf
```

## Notes

- None of these models are currently available in GGUF format for LM Studio/Ollama
- They require direct Python integration via Hugging Face Transformers
- All require GPU for reasonable performance (CPU inference is very slow)
- RTX 5080 (16GB VRAM) can handle all recommended models
