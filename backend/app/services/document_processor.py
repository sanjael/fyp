import os
import pdfplumber
from datetime import datetime
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

def extract_text_from_pdf(file_path: str) -> str:
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Error extracting text from {file_path}: {e}")
    return text

def chunk_document(text: str, filename: str, extra_metadata: dict = None) -> list[Document]:
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        length_function=len,
    )
    
    # We add metadata like filename, ingestion date, and document provenance for tracking
    chunks = text_splitter.split_text(text)
    
    documents = []
    current_date = datetime.now().isoformat()
    
    base_metadata = {
        "filename": filename,
        "ingestion_date": current_date
    }
    if extra_metadata and isinstance(extra_metadata, dict):
        base_metadata.update(extra_metadata)
    
    for i, chunk in enumerate(chunks):
        doc_meta = base_metadata.copy()
        doc_meta["chunk_index"] = i
        doc = Document(
            page_content=chunk,
            metadata=doc_meta
        )
        documents.append(doc)
        
    return documents

