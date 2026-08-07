import os
import shutil
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from pydantic import BaseModel
from datetime import datetime
from ..services.document_processor import extract_text_from_pdf, chunk_document
from ..services.vector_store import add_documents_to_chroma, delete_documents_by_filename

router = APIRouter()

import json

METADATA_FILE = os.path.join("uploads", "documents_metadata.json")

def load_uploaded_docs() -> list[dict]:
    if os.path.exists(METADATA_FILE):
        try:
            with open(METADATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def save_uploaded_docs():
    os.makedirs("uploads", exist_ok=True)
    try:
        with open(METADATA_FILE, "w", encoding="utf-8") as f:
            json.dump(UPLOADED_DOCS, f, indent=2)
    except Exception as e:
        print(f"Error saving metadata: {e}")

UPLOADED_DOCS = load_uploaded_docs()


class DocResponse(BaseModel):
    id: int
    name: str
    date: str
    chunks: int
    status: str

def process_document_task(file_path: str, doc_id: int, filename: str):
    try:
        # 1. Extract text
        text = extract_text_from_pdf(file_path)
        # 2. Chunk text
        chunks = chunk_document(text, filename)
        # 3. Embed and store in Chroma
        add_documents_to_chroma(chunks)
        
        # Update status
        for doc in UPLOADED_DOCS:
            if doc["id"] == doc_id:
                doc["chunks"] = len(chunks)
                doc["status"] = "processed"
                break
        save_uploaded_docs()
    except Exception as e:
        print(f"Error processing doc: {e}")
        for doc in UPLOADED_DOCS:
            if doc["id"] == doc_id:
                doc["status"] = "failed"
                break
        save_uploaded_docs()


@router.post("/upload")
async def upload_document(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    # Save file temporarily
    os.makedirs("uploads", exist_ok=True)
    file_path = f"uploads/{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    doc_id = len(UPLOADED_DOCS) + 1
    new_doc = {
        "id": doc_id,
        "name": file.filename,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "chunks": 0,
        "status": "processing"
    }
    UPLOADED_DOCS.append(new_doc)
    save_uploaded_docs()
    
    # Run processing in background
    background_tasks.add_task(process_document_task, file_path, doc_id, file.filename)
    
    return {"message": "Upload successful, processing started", "doc": new_doc}

@router.get("/list", response_model=list[DocResponse])
async def list_documents():
    return UPLOADED_DOCS

@router.delete("/{doc_id}")
async def delete_document(doc_id: int):
    global UPLOADED_DOCS
    target_doc = None
    for doc in UPLOADED_DOCS:
        if doc["id"] == doc_id:
            target_doc = doc
            break

    if not target_doc:
        raise HTTPException(status_code=404, detail="Document not found")

    filename = target_doc["name"]
    delete_documents_by_filename(filename)

    file_path = f"uploads/{filename}"
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception:
            pass

    UPLOADED_DOCS = [doc for doc in UPLOADED_DOCS if doc["id"] != doc_id]
    save_uploaded_docs()

    return {"message": "Document deleted successfully", "doc_id": doc_id}

