#!/usr/bin/env python3
"""
OCR Test Script
Simple command-line tool to test OCR processing
"""

import sys
import argparse
from pathlib import Path

# Import our OCR processor
from ocr_processor import OCRProcessor, OCR_MODELS


def print_models():
    """Print available OCR models"""
    print("\n" + "="*70)
    print("Available OCR Models:")
    print("="*70)

    for key, info in OCR_MODELS.items():
        print(f"\n{key}:")
        print(f"  Name: {info['name']}")
        print(f"  Description: {info['description']}")
        print(f"  Memory: {info['memory']}")
        print(f"  Speed: {info['speed']}")
        print(f"  Quality: {info['quality']}")

    print("\n" + "="*70)


def check_deps():
    """Check if dependencies are installed"""
    print("Checking dependencies...")

    missing = OCRProcessor.check_dependencies()

    if missing:
        print("\n❌ Missing dependencies:")
        for pkg in missing:
            print(f"   - {pkg}")
        print("\nInstall with:")
        print(f"   pip install {' '.join(missing)}")
        return False
    else:
        print("✅ All dependencies installed!")
        return True


def main():
    parser = argparse.ArgumentParser(description="Test OCR processing on PDF files")
    parser.add_argument("pdf_file", nargs="?", help="Path to PDF file to process")
    parser.add_argument("--model", "-m", default="qwen2-vl-2b",
                       choices=list(OCR_MODELS.keys()),
                       help="OCR model to use (default: qwen2-vl-2b)")
    parser.add_argument("--output", "-o", help="Output text file (default: {pdf_name}_OCR.txt)")
    parser.add_argument("--dpi", type=int, default=300, help="Image DPI (default: 300)")
    parser.add_argument("--list-models", action="store_true", help="List available models and exit")
    parser.add_argument("--check-deps", action="store_true", help="Check dependencies and exit")

    args = parser.parse_args()

    # List models
    if args.list_models:
        print_models()
        return 0

    # Check dependencies
    if args.check_deps:
        check_deps()
        return 0

    # Require PDF file
    if not args.pdf_file:
        parser.print_help()
        print("\n" + "="*70)
        print("Quick Start:")
        print("="*70)
        print("1. Check dependencies:")
        print("   python test_ocr.py --check-deps")
        print("\n2. List available models:")
        print("   python test_ocr.py --list-models")
        print("\n3. Process a PDF:")
        print("   python test_ocr.py path/to/your.pdf")
        print("\n4. Use specific model:")
        print("   python test_ocr.py path/to/your.pdf --model got-ocr")
        print("="*70 + "\n")
        return 1

    # Check if file exists
    pdf_path = Path(args.pdf_file)
    if not pdf_path.exists():
        print(f"❌ Error: File not found: {pdf_path}")
        return 1

    # Set output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = pdf_path.parent / f"{pdf_path.stem}_OCR.txt"

    # Check dependencies first
    print("="*70)
    print("OCR Test Script")
    print("="*70)
    print(f"PDF File: {pdf_path}")
    print(f"Model: {OCR_MODELS[args.model]['name']}")
    print(f"Output: {output_path}")
    print("="*70 + "\n")

    if not check_deps():
        print("\n❌ Cannot proceed without dependencies.")
        return 1

    print("\n" + "="*70)
    print("Starting OCR Processing")
    print("="*70)

    # Initialize processor
    print(f"\n1. Initializing OCR processor with {args.model}...")
    processor = OCRProcessor(model_key=args.model)

    # Load model
    print(f"\n2. Loading model (this may take a while on first run)...")
    print("   ⏳ Downloading model if needed...")
    print("   ⏳ Loading into GPU memory...")

    def progress_callback(message):
        print(f"   {message}")

    try:
        processor.load_model(progress_callback=progress_callback)
        print("\n   ✅ Model loaded successfully!")
    except Exception as e:
        print(f"\n   ❌ Error loading model: {e}")
        print("\nTroubleshooting:")
        print("- Make sure you have a CUDA-capable GPU")
        print("- Check you have enough VRAM (see model requirements)")
        print("- Ensure PyTorch is installed with CUDA support")
        print("  pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118")
        return 1

    # Process PDF
    print(f"\n3. Processing PDF...")
    print(f"   Converting pages to images (DPI: {args.dpi})...")

    try:
        extracted_text = processor.process_pdf(str(pdf_path), progress_callback=progress_callback)
        print(f"\n   ✅ OCR complete!")
    except Exception as e:
        print(f"\n   ❌ Error during OCR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Save output
    print(f"\n4. Saving output to {output_path}...")
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(extracted_text)

        # Show statistics
        char_count = len(extracted_text)
        line_count = extracted_text.count('\n') + 1
        word_count = len(extracted_text.split())

        print(f"\n   ✅ Saved successfully!")
        print(f"\n   Statistics:")
        print(f"   - Characters: {char_count:,}")
        print(f"   - Lines: {line_count:,}")
        print(f"   - Words: {word_count:,}")

        # Show preview
        preview_length = 500
        preview = extracted_text[:preview_length]
        if len(extracted_text) > preview_length:
            preview += "..."

        print(f"\n   Preview (first {preview_length} chars):")
        print("   " + "-"*66)
        for line in preview.split('\n')[:10]:
            print(f"   {line}")
        print("   " + "-"*66)

    except Exception as e:
        print(f"\n   ❌ Error saving output: {e}")
        return 1

    print("\n" + "="*70)
    print("✅ OCR PROCESSING COMPLETE!")
    print("="*70)
    print(f"\nOutput saved to: {output_path}")
    print("\nNext steps:")
    print("1. Review the output file for accuracy")
    print("2. If needed, apply post-processing with:")
    print(f"   python tts_preprocessor_gui.py")
    print("   Then click 'Pre-clean Input' on the text file")
    print("="*70 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
