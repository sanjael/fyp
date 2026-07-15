"""
Document Processor Module
Handles PDF loading, text extraction, and intelligent chunking.
"""

import os
import re
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple

import pdfplumber
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter

import config


class DocumentChunk:
    """Represents a processed chunk of text from a document."""
    
    def __init__(
        self,
        chunk_id: str,
        text: str,
        source: str,
        page_number: int,
        chunk_index: int,
        metadata: Dict,
    ):
        self.chunk_id = chunk_id
        self.text = text
        self.source = source
        self.page_number = page_number
        self.chunk_index = chunk_index
        self.metadata = metadata

    def to_dict(self) -> Dict:
        return {
            "chunk_id": self.chunk_id,
            "text": self.text,
            "source": self.source,
            "page_number": self.page_number,
            "chunk_index": self.chunk_index,
            **self.metadata,
        }


class DocumentProcessor:
    """
    Processes PDF documents into indexed chunks for the RAGShield pipeline.
    Extracts text, metadata, and prepares chunks for embedding.
    """

    def __init__(self):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def extract_text_from_pdf(self, pdf_path: str) -> Tuple[str, Dict]:
        """
        Extract full text and metadata from a PDF file.
        Uses pdfplumber first (better accuracy), falls back to pypdf.
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        full_text = ""
        page_texts = []
        metadata = {}

        # Try pdfplumber first (better for tables and complex layouts)
        try:
            with pdfplumber.open(str(pdf_path)) as pdf:
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text() or ""
                    page_texts.append({"page": i + 1, "text": text})
                    full_text += text + "\n\n"

                # Extract metadata from pdfplumber
                if pdf.metadata:
                    metadata = {
                        "title": pdf.metadata.get("Title", pdf_path.stem),
                        "author": pdf.metadata.get("Author", "Unknown"),
                        "creation_date": str(pdf.metadata.get("CreationDate", "")),
                        "num_pages": len(pdf.pages),
                    }
        except Exception:
            # Fallback to pypdf
            reader = PdfReader(str(pdf_path))
            for i, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                page_texts.append({"page": i + 1, "text": text})
                full_text += text + "\n\n"

            pdf_meta = reader.metadata or {}
            metadata = {
                "title": pdf_meta.get("/Title", pdf_path.stem),
                "author": pdf_meta.get("/Author", "Unknown"),
                "creation_date": str(pdf_meta.get("/CreationDate", "")),
                "num_pages": len(reader.pages),
            }

        metadata["filename"] = pdf_path.name
        metadata["filepath"] = str(pdf_path)
        metadata["file_size_kb"] = round(pdf_path.stat().st_size / 1024, 2)
        metadata["source_type"] = self._detect_source_type(pdf_path.name, full_text)
        metadata["year"] = self._extract_year(full_text, metadata.get("creation_date", ""))
        metadata["page_texts"] = page_texts

        return full_text, metadata

    def _detect_source_type(self, filename: str, text: str) -> str:
        """Detect the type of document based on filename and content."""
        filename_lower = filename.lower()
        text_lower = text[:2000].lower()

        if any(kw in text_lower for kw in ["abstract", "arxiv", "doi:", "proceedings", "journal"]):
            return "research_paper"
        elif "wikipedia" in filename_lower or "wikipedia" in text_lower:
            return "wikipedia"
        elif any(kw in filename_lower for kw in ["textbook", "book", "chapter"]):
            return "textbook"
        elif any(kw in filename_lower for kw in ["gov", "government", "policy"]):
            return "government"
        else:
            return "unknown"

    def _extract_year(self, text: str, creation_date: str) -> int:
        """Extract the publication year from text or metadata."""
        current_year = datetime.now().year

        # Try from creation_date metadata
        if creation_date:
            year_match = re.search(r"(20\d{2}|19\d{2})", creation_date)
            if year_match:
                return int(year_match.group(1))

        # Try from first 2000 chars of text
        year_match = re.search(r"\b(20\d{2}|19\d{2})\b", text[:2000])
        if year_match:
            year = int(year_match.group(1))
            if 1990 <= year <= current_year:
                return year

        return current_year  # Default to current year

    def chunk_document(
        self, full_text: str, metadata: Dict
    ) -> List[DocumentChunk]:
        """
        Split document text into overlapping chunks with metadata.
        """
        # Clean the text
        clean_text = self._clean_text(full_text)

        # Split into chunks
        raw_chunks = self.splitter.split_text(clean_text)

        chunks = []
        for i, chunk_text in enumerate(raw_chunks):
            if len(chunk_text.strip()) < 50:  # Skip very short chunks
                continue

            # Generate unique chunk ID
            chunk_id = hashlib.md5(
                f"{metadata['filename']}_{i}_{chunk_text[:50]}".encode()
            ).hexdigest()

            chunk = DocumentChunk(
                chunk_id=chunk_id,
                text=chunk_text.strip(),
                source=metadata["filename"],
                page_number=self._estimate_page(i, len(raw_chunks), metadata.get("num_pages", 1)),
                chunk_index=i,
                metadata={
                    "title": metadata.get("title", ""),
                    "author": metadata.get("author", "Unknown"),
                    "year": metadata.get("year", datetime.now().year),
                    "source_type": metadata.get("source_type", "unknown"),
                    "filepath": metadata.get("filepath", ""),
                    "file_size_kb": metadata.get("file_size_kb", 0),
                },
            )
            chunks.append(chunk)

        return chunks

    def _clean_text(self, text: str) -> str:
        """Clean extracted PDF text."""
        # Remove excessive whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" {2,}", " ", text)
        # Remove page numbers patterns
        text = re.sub(r"\n\d+\n", "\n", text)
        # Remove headers/footers (short isolated lines)
        lines = text.split("\n")
        cleaned = []
        for line in lines:
            stripped = line.strip()
            if stripped and (len(stripped) > 3 or stripped.isdigit() is False):
                cleaned.append(stripped)
        return "\n".join(cleaned)

    def _estimate_page(self, chunk_index: int, total_chunks: int, num_pages: int) -> int:
        """Estimate which page a chunk is from."""
        if total_chunks == 0:
            return 1
        return max(1, round((chunk_index / total_chunks) * num_pages))

    def process_pdf(self, pdf_path: str) -> Tuple[List[DocumentChunk], Dict]:
        """
        Full pipeline: PDF → extracted text → chunks with metadata.
        Returns chunks and document metadata.
        """
        print(f"[DocumentProcessor] Processing: {pdf_path}")
        full_text, metadata = self.extract_text_from_pdf(pdf_path)
        chunks = self.chunk_document(full_text, metadata)
        print(f"[DocumentProcessor] Created {len(chunks)} chunks from {metadata['filename']}")
        return chunks, metadata

    def get_document_stats(self, pdf_path: str) -> Dict:
        """Get quick stats about a PDF without full processing."""
        try:
            reader = PdfReader(pdf_path)
            return {
                "filename": Path(pdf_path).name,
                "num_pages": len(reader.pages),
                "file_size_kb": round(Path(pdf_path).stat().st_size / 1024, 2),
            }
        except Exception as e:
            return {"error": str(e)}
