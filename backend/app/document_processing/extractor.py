import os
from typing import Dict, Any, List
import pymupdf as fitz
from pypdf import PdfReader
from PIL import Image


class DocumentExtractionError(Exception):
    pass


class DocumentExtractor:
    """Extracts text and per-page content from medical documents (PDFs, images, text)."""

    @staticmethod
    def extract(file_path: str) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            raise DocumentExtractionError(f"File not found: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".pdf":
            return DocumentExtractor._extract_pdf(file_path)
        elif ext in [".txt", ".md", ".json", ".csv"]:
            return DocumentExtractor._extract_text_file(file_path)
        elif ext in [".png", ".jpg", ".jpeg", ".webp", ".tiff"]:
            return DocumentExtractor._extract_image(file_path)
        else:
            raise DocumentExtractionError(f"Unsupported document format: {ext}. Please upload a PDF, text, or image file.")

    @staticmethod
    def _extract_pdf(file_path: str) -> Dict[str, Any]:
        pages_content: List[Dict[str, Any]] = []
        full_text_parts: List[str] = []

        try:
            doc = fitz.open(file_path)
            page_count = len(doc)

            for page_num in range(page_count):
                page = doc[page_num]
                text = page.get_text("text") or ""
                clean_text = text.strip()

                pages_content.append({
                    "page_num": page_num + 1,
                    "text": clean_text
                })
                if clean_text:
                    full_text_parts.append(clean_text)

            doc.close()

            # Fallback with pypdf if PyMuPDF returned completely empty text
            if not any(p["text"] for p in pages_content):
                reader = PdfReader(file_path)
                pages_content = []
                full_text_parts = []
                for idx, page in enumerate(reader.pages):
                    p_text = (page.extract_text() or "").strip()
                    pages_content.append({
                        "page_num": idx + 1,
                        "text": p_text
                    })
                    if p_text:
                        full_text_parts.append(p_text)

            full_text = "\n\n--- Page Break ---\n\n".join(full_text_parts)

            return {
                "full_text": full_text,
                "page_count": max(len(pages_content), 1),
                "pages": pages_content,
                "is_scanned": len(full_text.strip()) == 0
            }

        except Exception as e:
            raise DocumentExtractionError(f"Failed to read PDF document: {str(e)}")

    @staticmethod
    def _extract_text_file(file_path: str) -> Dict[str, Any]:
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read().strip()
            return {
                "full_text": content,
                "page_count": 1,
                "pages": [{"page_num": 1, "text": content}],
                "is_scanned": False
            }
        except Exception as e:
            raise DocumentExtractionError(f"Failed to read text document: {str(e)}")

    @staticmethod
    def _extract_image(file_path: str) -> Dict[str, Any]:
        try:
            # Verify image integrity
            with Image.open(file_path) as img:
                width, height = img.size
                format_name = img.format

            # Note: For scanned image documents without Tesseract binary on Windows,
            # we provide a clean image description note or Gemini multimodal extraction.
            text_placeholder = f"[Scanned Image Document: {os.path.basename(file_path)} | Dimensions: {width}x{height} | Format: {format_name}]"
            return {
                "full_text": text_placeholder,
                "page_count": 1,
                "pages": [{"page_num": 1, "text": text_placeholder}],
                "is_scanned": True
            }
        except Exception as e:
            raise DocumentExtractionError(f"Failed to process image file: {str(e)}")
