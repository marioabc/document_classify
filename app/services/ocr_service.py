import easyocr
import logging
from typing import List, Tuple
from PIL import Image
import numpy as np
from pathlib import Path
from app.config import settings

logger = logging.getLogger(__name__)

try:
    from pdf2image import convert_from_path
    PDF_SUPPORT = True
    logger.info("PDF support enabled (pdf2image available)")
except ImportError:
    PDF_SUPPORT = False
    logger.warning("PDF support disabled (pdf2image not installed)")


class OCRService:
    def __init__(self):
        logger.info(f"Initializing EasyOCR with languages: {settings.ocr_languages_list}")
        self.reader = easyocr.Reader(
            settings.ocr_languages_list,
            gpu=settings.OCR_GPU
        )

    def extract_text(self, image_path: str) -> Tuple[str, List[str]]:
        """
        Extract text from image or PDF
        Returns: (full_text, list_of_lines)
        """
        try:
            file_path = Path(image_path)
            logger.info(f"Processing file: {image_path}")

            # Check if it's a PDF
            if file_path.suffix.lower() == '.pdf':
                if not PDF_SUPPORT:
                    raise RuntimeError("PDF support not available. Install pdf2image: pip install pdf2image")

                logger.info("📄 Detected PDF file - converting to images")
                return self._extract_text_from_pdf(image_path)
            else:
                # Regular image processing
                logger.info("🖼️  Processing as image")
                return self._extract_text_from_image(image_path)

        except Exception as e:
            logger.error(f"Error during OCR processing: {str(e)}")
            raise

    def _extract_text_from_image(self, image_path: str) -> Tuple[str, List[str]]:
        """Extract text from a single image"""
        # Read image
        image = Image.open(image_path)
        image_np = np.array(image)

        # Perform OCR
        results = self.reader.readtext(image_np, detail=0)

        # Join results
        full_text = ' '.join(results)

        logger.info(f"Extracted {len(results)} text segments from image")
        return full_text, results

    def _extract_text_from_pdf(self, pdf_path: str) -> Tuple[str, List[str]]:
        """Extract text from PDF by converting pages to images"""
        logger.info(f"Converting PDF to images: {pdf_path}")

        # Convert PDF to images (one image per page)
        images = convert_from_path(pdf_path, dpi=200)
        logger.info(f"📄 PDF has {len(images)} page(s)")

        all_text_segments = []
        full_text_parts = []

        # Process each page
        for page_num, image in enumerate(images, 1):
            logger.info(f"Processing page {page_num}/{len(images)}")

            # Convert PIL Image to numpy array
            image_np = np.array(image)

            # Perform OCR on this page
            results = self.reader.readtext(image_np, detail=0)

            if results:
                page_text = ' '.join(results)
                full_text_parts.append(page_text)
                all_text_segments.extend(results)
                logger.info(f"  → Extracted {len(results)} text segments from page {page_num}")

        # Combine all pages
        full_text = ' '.join(full_text_parts)
        logger.info(f"✅ Total extracted {len(all_text_segments)} text segments from {len(images)} page(s)")

        return full_text, all_text_segments

    def preprocess_image(self, image_path: str) -> str:
        """
        Preprocess image for better OCR results
        Can be extended with more preprocessing steps
        """
        # Placeholder for image preprocessing
        # You can add: denoise, contrast adjustment, deskewing, etc.
        return image_path


# Singleton instance
ocr_service = OCRService()
