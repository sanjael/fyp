import os
import shutil
from fastapi import APIRouter, UploadFile, File, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime
from ..services.document_processor import extract_text_from_pdf, chunk_document
from ..services.vector_store import add_documents_to_chroma

router = APIRouter()

# In-memory storage for MVP
UPLOADED_DOCS = [
    {"id": 1, "name": "attention_is_all_you_need.pdf", "date": "2023-10-12", "chunks": 145, "status": "processed"},
]

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
    except Exception as e:
        print(f"Error processing doc: {e}")
        for doc in UPLOADED_DOCS:
            if doc["id"] == doc_id:
                doc["status"] = "failed"
                break

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
    
    # Run processing in background
    background_tasks.add_task(process_document_task, file_path, doc_id, file.filename)
    
    return {"message": "Upload successful, processing started", "doc": new_doc}

@router.get("/list", response_model=list[DocResponse])
async def list_documents():
    return UPLOADED_DOCS
