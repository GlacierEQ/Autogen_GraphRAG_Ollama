"""
PDF document processor for GraphRAG integration.
Allows ingestion of PDF files into the knowledge graph.
"""
import os
import tempfile
from typing import Dict, List, Optional, Any
import fitz  # PyMuPDF
import logging
import re
from PIL import Image
import pytesseract
import numpy as np

logger = logging.getLogger(__name__)

class PDFDocumentProcessor:
    """Process PDF documents for GraphRAG indexing."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the PDF document processor with optional configuration."""
        self.config = config or {}
        self.ocr_enabled = self.config.get("ocr_enabled", True)
        self.ocr_language = self.config.get("ocr_language", "eng")
        self.chunk_size = self.config.get("chunk_size", 300)
        self.chunk_overlap = self.config.get("chunk_overlap", 100)
        self.extract_images = self.config.get("extract_images", False)
        self.image_dpi = self.config.get("image_dpi", 300)
    
    def extract_text(self, file_path: str) -> str:
        """Extract text content from a PDF document."""
        try:
            doc = fitz.open(file_path)
            full_text = []
            
            for page_num, page in enumerate(doc):
                text = page.get_text()
                
                # If page has no text or very little text, try OCR
                if self.ocr_enabled and (not text.strip() or len(text) < 50):
                    logger.info(f"Using OCR for page {page_num+1} in {file_path}")
                    text = self._extract_text_with_ocr(page)
                
                full_text.append(text)
            
            return "\n\n".join(full_text)
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            return f"Error: Could not extract text from document ({str(e)})"
    
    def _extract_text_with_ocr(self, page) -> str:
        """Extract text from a page using OCR."""
        try:
            # Render page to an image
            pix = page.get_pixmap(matrix=fitz.Matrix(self.image_dpi/72, self.image_dpi/72))
            
            # Convert to PIL Image
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            # Apply OCR
            text = pytesseract.image_to_string(img, lang=self.ocr_language)
            return text
        except Exception as e:
            logger.error(f"OCR error: {str(e)}")
            return ""
    
    def extract_metadata(self, file_path: str) -> Dict[str, str]:
        """Extract metadata from a PDF document."""
        try:
            doc = fitz.open(file_path)
            metadata = {}
            
            # Standard PDF metadata
            meta = doc.metadata
            if meta:
                if meta.get("title"):
                    metadata["title"] = meta["title"]
                if meta.get("author"):
                    metadata["author"] = meta["author"]
                if meta.get("subject"):
                    metadata["subject"] = meta["subject"]
                if meta.get("keywords"):
                    metadata["keywords"] = meta["keywords"]
                if meta.get("creationDate"):
                    metadata["created"] = meta["creationDate"]
                if meta.get("modDate"):
                    metadata["modified"] = meta["modDate"]
            
            # Document statistics
            metadata["page_count"] = str(doc.page_count)
            metadata["file_size"] = str(os.path.getsize(file_path))
            
            # Extract text
            full_text = self.extract_text(file_path)
            metadata["word_count"] = str(len(re.findall(r'\b\w+\b', full_text)))
            
            return metadata
        except Exception as e:
            logger.error(f"Error extracting metadata from PDF: {str(e)}")
            return {"error": f"Could not extract metadata ({str(e)})"}
    
    def convert_to_markdown(self, file_path: str, output_dir: str) -> str:
        """Convert PDF document to Markdown format for GraphRAG indexing."""
        filename = os.path.basename(file_path)
        name, _ = os.path.splitext(filename)
        output_path = os.path.join(output_dir, f"{name}.md")
        
        try:
            doc = fitz.open(file_path)
            
            with open(output_path, "w", encoding="utf-8") as md_file:
                # Add metadata as YAML frontmatter
                metadata = self.extract_metadata(file_path)
                md_file.write("---\n")
                for key, value in metadata.items():
                    if value and str(value).strip():
                        md_file.write(f"{key}: {value}\n")
                md_file.write("---\n\n")
                
                # Add title
                title = metadata.get("title", name)
                md_file.write(f"# {title}\n\n")
                
                # Process each page
                for page_num, page in enumerate(doc):
                    md_file.write(f"## Page {page_num+1}\n\n")
                    
                    # Extract text
                    text = page.get_text()
                    if not text.strip() or len(text) < 50:
                        if self.ocr_enabled:
                            text = self._extract_text_with_ocr(page)
                    
                    # Clean up text
                    text = re.sub(r'\n{3,}', '\n\n', text)  # Remove excess newlines
                    paragraphs = text.split('\n\n')
                    
                    for paragraph in paragraphs:
                        if paragraph.strip():
                            md_file.write(f"{paragraph.strip()}\n\n")
                    
                    # Extract images if enabled
                    if self.extract_images:
                        img_dir = os.path.join(output_dir, f"{name}_images")
                        os.makedirs(img_dir, exist_ok=True)
                        
                        # Extract images from the page
                        image_list = page.get_images(full=True)
                        for img_idx, img_info in enumerate(image_list):
                            xref = img_info[0]
                            base_img = doc.extract_image(xref)
                            image_data = base_img["image"]
                            
                            # Save the image
                            img_filename = f"page{page_num+1}_img{img_idx+1}.png"
                            img_path = os.path.join(img_dir, img_filename)
                            with open(img_path, "wb") as img_file:
                                img_file.write(image_data)
                            
                            # Add image reference to markdown
                            rel_path = os.path.join(f"{name}_images", img_filename)
                            md_file.write(f"![Image {img_idx+1} from page {page_num+1}]({rel_path})\n\n")
            
            return output_path
        except Exception as e:
            logger.error(f"Error converting PDF to Markdown: {str(e)}")
            return f"Error: Could not convert document to Markdown ({str(e)})"

    def process_directory(self, input_dir: str, output_dir: str) -> List[str]:
        """Process all PDF documents in a directory."""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        processed_files = []
        
        for root, _, files in os.walk(input_dir):
            for file in files:
                if file.lower().endswith('.pdf'):
                    file_path = os.path.join(root, file)
                    result = self.convert_to_markdown(file_path, output_dir)
                    if not result.startswith("Error"):
                        processed_files.append(result)
        
        return processed_files

# Command line interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Process PDF documents for GraphRAG")
    parser.add_argument("--input", "-i", required=True, help="Input directory or file")
    parser.add_argument("--output", "-o", required=True, help="Output directory for Markdown files")
    parser.add_argument("--ocr", action="store_true", help="Enable OCR for text extraction")
    args = parser.parse_args()
    
    processor = PDFDocumentProcessor({"ocr_enabled": args.ocr})
    
    if os.path.isdir(args.input):
        results = processor.process_directory(args.input, args.output)
        print(f"Processed {len(results)} files")
        for result in results:
            print(f"  - {result}")
    else:
        result = processor.convert_to_markdown(args.input, args.output)
        print(f"Result: {result}")
