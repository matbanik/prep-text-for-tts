"""
OCR Processing Module
Handles PDF to text extraction using various OCR models
"""

import os
from pathlib import Path
from typing import List, Optional, Tuple
from PIL import Image
import io

# ============================================================================
# OCR MODEL CONFIGURATIONS
# ============================================================================

OCR_MODELS = {
    "qwen2-vl-2b": {
        "name": "Qwen2-VL-2B (Recommended)",
        "hf_model": "Qwen/Qwen2-VL-2B-Instruct",
        "description": "Fast, excellent accuracy, 90+ languages",
        "memory": "~8GB VRAM",
        "speed": "Fast",
        "quality": "Excellent"
    },
    "qwen2-vl-7b": {
        "name": "Qwen2-VL-7B (Best Quality)",
        "hf_model": "Qwen/Qwen2-VL-7B-Instruct",
        "description": "Best overall quality, slower than 2B",
        "memory": "~16GB VRAM",
        "speed": "Medium",
        "quality": "Exceptional"
    },
    "got-ocr": {
        "name": "GOT-OCR2.0 (Lightweight)",
        "hf_model": "ucaslcl/GOT-OCR2_0",
        "description": "Lightweight, OCR-specific, very fast",
        "memory": "~4GB VRAM",
        "speed": "Very Fast",
        "quality": "Good"
    },
    "minicpm-o": {
        "name": "MiniCPM-o-2.6 (Top Accuracy)",
        "hf_model": "openbmb/MiniCPM-o-2_6",
        "description": "#1 OCRBench, beats GPT-4o",
        "memory": "~12GB VRAM",
        "speed": "Medium",
        "quality": "Best"
    }
}


class OCRProcessor:
    """Handles OCR processing for PDFs"""

    def __init__(self, model_key="qwen2-vl-2b"):
        """
        Initialize OCR processor

        Args:
            model_key: Key from OCR_MODELS dict
        """
        self.model_key = model_key
        self.model = None
        self.processor = None
        self.tokenizer = None
        self.model_loaded = False

    @staticmethod
    def check_dependencies():
        """Check if required packages are installed"""
        missing = []

        try:
            import transformers
        except ImportError:
            missing.append("transformers")

        try:
            import torch
        except ImportError:
            missing.append("torch")

        try:
            import PIL
        except ImportError:
            missing.append("pillow")

        # PDF handling
        try:
            import fitz  # PyMuPDF
        except ImportError:
            missing.append("pymupdf")

        return missing

    def load_model(self, progress_callback=None):
        """Load the selected OCR model"""
        if progress_callback:
            progress_callback(f"Loading {OCR_MODELS[self.model_key]['name']}...")

        try:
            if self.model_key.startswith("qwen2-vl"):
                self._load_qwen2_vl(progress_callback)
            elif self.model_key == "got-ocr":
                self._load_got_ocr(progress_callback)
            elif self.model_key == "minicpm-o":
                self._load_minicpm(progress_callback)
            else:
                raise ValueError(f"Unknown model key: {self.model_key}")

            self.model_loaded = True
            if progress_callback:
                progress_callback("Model loaded successfully!")

        except Exception as e:
            if progress_callback:
                progress_callback(f"Error loading model: {str(e)}")
            raise

    def _load_qwen2_vl(self, progress_callback=None):
        """Load Qwen2-VL model"""
        from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
        import torch

        model_name = OCR_MODELS[self.model_key]["hf_model"]

        if progress_callback:
            progress_callback(f"Downloading {model_name}...")

        self.model = Qwen2VLForConditionalGeneration.from_pretrained(
            model_name,
            torch_dtype=torch.bfloat16,
            device_map="auto"
        )

        self.processor = AutoProcessor.from_pretrained(model_name)

        if progress_callback:
            progress_callback("Model loaded into GPU memory")

    def _load_got_ocr(self, progress_callback=None):
        """Load GOT-OCR2.0 model"""
        from transformers import AutoModel, AutoTokenizer

        model_name = OCR_MODELS[self.model_key]["hf_model"]

        if progress_callback:
            progress_callback(f"Downloading {model_name}...")

        self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        self.model = AutoModel.from_pretrained(
            model_name,
            trust_remote_code=True,
            low_cpu_mem_usage=True,
            device_map="auto",
            use_safetensors=True
        )

        if progress_callback:
            progress_callback("GOT-OCR2.0 loaded successfully")

    def _load_minicpm(self, progress_callback=None):
        """Load MiniCPM-o model"""
        from transformers import AutoModel, AutoTokenizer

        model_name = OCR_MODELS[self.model_key]["hf_model"]

        if progress_callback:
            progress_callback(f"Downloading {model_name}...")

        self.model = AutoModel.from_pretrained(
            model_name,
            trust_remote_code=True,
            device_map="auto"
        )

        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            trust_remote_code=True
        )

        if progress_callback:
            progress_callback("MiniCPM-o loaded successfully")

    def extract_text_from_image(self, image_path: str) -> str:
        """Extract text from a single image using loaded OCR model"""
        if not self.model_loaded:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        try:
            if self.model_key.startswith("qwen2-vl"):
                return self._ocr_qwen2_vl(image_path)
            elif self.model_key == "got-ocr":
                return self._ocr_got(image_path)
            elif self.model_key == "minicpm-o":
                return self._ocr_minicpm(image_path)
        except Exception as e:
            raise RuntimeError(f"OCR failed: {str(e)}")

    def _ocr_qwen2_vl(self, image_path: str) -> str:
        """Run OCR using Qwen2-VL"""
        from qwen_vl_utils import process_vision_info
        import torch

        messages = [{
            "role": "user",
            "content": [
                {"type": "image", "image": image_path},
                {"type": "text", "text": "Extract all text from this image. Output only the text, preserving paragraphs and structure."}
            ]
        }]

        text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        image_inputs, video_inputs = process_vision_info(messages)

        inputs = self.processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt"
        ).to(self.model.device)

        with torch.no_grad():
            output_ids = self.model.generate(**inputs, max_new_tokens=4096)

        output_text = self.processor.batch_decode(
            output_ids,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False
        )[0]

        # Extract just the assistant's response
        if "<|im_start|>assistant" in output_text:
            output_text = output_text.split("<|im_start|>assistant")[-1]
        if "<|im_end|>" in output_text:
            output_text = output_text.split("<|im_end|>")[0]

        return output_text.strip()

    def _ocr_got(self, image_path: str) -> str:
        """Run OCR using GOT-OCR2.0"""
        # GOT-OCR uses chat interface
        result = self.model.chat(self.tokenizer, image_path, ocr_type='format')
        return result

    def _ocr_minicpm(self, image_path: str) -> str:
        """Run OCR using MiniCPM-o"""
        # Load image
        image = Image.open(image_path).convert('RGB')

        # Create message
        msgs = [{
            'role': 'user',
            'content': "Extract all text from this image, preserving paragraph structure."
        }]

        # Run inference
        res = self.model.chat(
            image=image,
            msgs=msgs,
            tokenizer=self.tokenizer
        )

        return res

    @staticmethod
    def pdf_to_images(pdf_path: str, output_dir: Optional[str] = None, dpi: int = 300) -> List[str]:
        """
        Convert PDF pages to images

        Args:
            pdf_path: Path to PDF file
            output_dir: Directory to save images (temp dir if None)
            dpi: Resolution for rendering (default 300)

        Returns:
            List of image file paths
        """
        import fitz  # PyMuPDF

        pdf_path = Path(pdf_path)

        if output_dir is None:
            output_dir = pdf_path.parent / f"{pdf_path.stem}_pages"

        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)

        doc = fitz.open(pdf_path)
        image_paths = []

        for page_num in range(len(doc)):
            page = doc[page_num]

            # Render page to image
            # Zoom factor for desired DPI (72 is default)
            zoom = dpi / 72
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)

            # Save image
            image_path = output_dir / f"page_{page_num + 1:04d}.png"
            pix.save(str(image_path))
            image_paths.append(str(image_path))

        doc.close()

        return image_paths

    def process_pdf(self, pdf_path: str, progress_callback=None) -> str:
        """
        Process entire PDF file

        Args:
            pdf_path: Path to PDF file
            progress_callback: Function to call with progress updates

        Returns:
            Extracted text from all pages
        """
        if not self.model_loaded:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        # Convert PDF to images
        if progress_callback:
            progress_callback("Converting PDF to images...")

        image_paths = self.pdf_to_images(pdf_path)
        total_pages = len(image_paths)

        if progress_callback:
            progress_callback(f"Processing {total_pages} pages...")

        # Process each page
        all_text = []

        for i, image_path in enumerate(image_paths, 1):
            if progress_callback:
                progress_callback(f"OCR processing page {i}/{total_pages}...")

            try:
                page_text = self.extract_text_from_image(image_path)
                all_text.append(page_text)

                if progress_callback:
                    progress_callback(f"Page {i}/{total_pages} complete ({len(page_text)} chars)")

            except Exception as e:
                if progress_callback:
                    progress_callback(f"Warning: Page {i} failed: {str(e)}")
                all_text.append(f"[ERROR ON PAGE {i}: {str(e)}]")

        # Combine all pages
        combined_text = "\n\n".join(all_text)

        return combined_text
