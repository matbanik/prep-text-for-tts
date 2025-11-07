"""
OCR Processing Module
Handles PDF to text extraction using LM Studio vision models
"""

import os
import base64
from pathlib import Path
from typing import List, Optional, Tuple
from PIL import Image
import io
import openai

# ============================================================================
# OCR MODEL CONFIGURATIONS (for LM Studio)
# ============================================================================

# Default OCR model for LM Studio
DEFAULT_OCR_MODEL = "qwen2-vl-7b-instruct"


class OCRProcessor:
    """Handles OCR processing for PDFs using LM Studio"""

    def __init__(self, lm_studio_host="http://localhost:1234/v1", model_name=None):
        """
        Initialize OCR processor for LM Studio

        Args:
            lm_studio_host: LM Studio API endpoint
            model_name: Model name loaded in LM Studio (e.g., "qwen2-vl-7b-instruct")
        """
        self.lm_studio_host = lm_studio_host
        self.model_name = model_name or DEFAULT_OCR_MODEL
        self.client = None

    @staticmethod
    def check_dependencies():
        """Check if required packages are installed"""
        missing = []

        try:
            import openai
        except ImportError:
            missing.append("openai")

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

    def connect(self, progress_callback=None):
        """Connect to LM Studio and verify vision model is loaded"""
        if progress_callback:
            progress_callback(f"Connecting to LM Studio at {self.lm_studio_host}...")

        try:
            # Create OpenAI client pointing to LM Studio
            self.client = openai.OpenAI(
                base_url=self.lm_studio_host,
                api_key="not-needed"  # LM Studio doesn't require API key
            )

            # Test connection with a simple text request
            if progress_callback:
                progress_callback("Testing connection...")

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )

            if progress_callback:
                progress_callback(f"✓ Connected to LM Studio successfully!")
                progress_callback(f"Model: {self.model_name}")

            return True

        except Exception as e:
            if progress_callback:
                progress_callback(f"✗ Connection failed: {str(e)}")
            raise RuntimeError(
                f"Failed to connect to LM Studio:\n{str(e)}\n\n"
                f"Make sure:\n"
                f"1. LM Studio is running\n"
                f"2. Local Server is started\n"
                f"3. {self.model_name} is loaded in LM Studio"
            )

    def extract_text_from_image(self, image_path: str) -> str:
        """Extract text from a single image using LM Studio vision model"""
        if not self.client:
            raise RuntimeError("Not connected. Call connect() first.")

        try:
            # Encode image as base64
            with open(image_path, 'rb') as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')

            # Determine image type
            image_ext = Path(image_path).suffix.lower()
            mime_types = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.webp': 'image/webp',
                '.gif': 'image/gif'
            }
            mime_type = mime_types.get(image_ext, 'image/jpeg')

            # Create vision message for LM Studio
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Extract all text from this image. Output only the text content, preserving paragraph structure and formatting. Do not add any commentary or explanations."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_data}"
                            }
                        }
                    ]
                }
            ]

            # Call LM Studio vision API
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=4096,
                temperature=0.1  # Low temperature for consistent OCR
            )

            # Extract response
            extracted_text = response.choices[0].message.content

            return extracted_text.strip()

        except Exception as e:
            raise RuntimeError(f"OCR failed: {str(e)}")

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
        if not self.client:
            raise RuntimeError("Not connected to LM Studio. Call connect() first.")

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
