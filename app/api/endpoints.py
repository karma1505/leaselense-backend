from fastapi import APIRouter, UploadFile, HTTPException
from pydantic import BaseModel
from app.services.vector_store import vector_store
from app.services.llm import llm_service
import shutil
import os
from typing import List

router = APIRouter()

class RiskAnalysisRequest(BaseModel):
    clause_text: str

class LetterRequest(BaseModel):
    risk_details: dict

@router.post("/upload")
async def upload_lease(file: UploadFile):
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = f"{upload_dir}/{file.filename}"
    print(f"[INFO] Uploading file: {file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    print(f"[SUCCESS] File saved to: {file_path}")
        
    return {"filename": file.filename, "status": "uploaded"}

from docling.document_converter import DocumentConverter
import re

def clean_text(text: str) -> str:
    # 1. Remove long underscores (form lines)
    text = re.sub(r'_{3,}', '', text)
    # 2. Collapse multiple newlines
    text = re.sub(r'\n\s*\n', '\n', text)
    # 3. Collapse multiple spaces (but keep newlines)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()

@router.post("/extract")
async def extract_text(filename: str):
    file_path = f"uploads/{filename}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
        
    try:
        print(f"[INFO] Extracting text from: {file_path} using Docling")
        converter = DocumentConverter()
        result = converter.convert(file_path)
        
        # Export to markdown for better structure preservation
        markdown_text = result.document.export_to_markdown()
        
        # Optional: Apply some cleaning if needed, but Markdown is usually cleaner
        cleaned_text = clean_text(markdown_text)
        
        # Estimate page count (Docling pages are in document.pages which is specific to the model, usually populated)
        page_count = len(result.document.pages) if hasattr(result.document, 'pages') else 0
        
        print(f"[SUCCESS] Extracted {len(cleaned_text)} chars from {file_path}.")
        
        return {
            "text": cleaned_text, 
            "raw_text_sample": markdown_text[:100] + "...",
            "page_count": page_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract text: {str(e)}")

@router.post("/analyze")
async def analyze_risk(request: RiskAnalysisRequest):
    print(f"[INFO] Analyzing lease text (length: {len(request.clause_text)})...")
    
    # 1. Split text into chunks (paragraphs)
    # Simple splitting by double newline
    paragraphs = [p.strip() for p in request.clause_text.split('\n\n') if len(p.strip()) > 50]
    
    # 2. Filter for relevant clauses (Security Deposit, Termination, Maintenance, etc.)
    idx_to_analyze = []
    keywords = ["deposit", "security", "refund", "termination", "notice", "repair", "maintenance", "increase", "rent"]
    
    for i, p in enumerate(paragraphs):
        if any(k in p.lower() for k in keywords):
            idx_to_analyze.append(i)
            
    # Limit to specific relevant chunks to save time/quota, or analyze all relevant ones?
    # Let's take up to 6 relevant chunks
    target_indices = idx_to_analyze[:6]
    
    results = []
    
    for i in target_indices:
        clause = paragraphs[i]
        print(f"[INFO] Analyzing chunk: {clause[:30]}...")
        
        # RAG
        relevant_laws = vector_store.query_similar(clause)
        law_context = " ".join([doc for doc in relevant_laws['documents'][0]]) if relevant_laws['documents'] else "No specific law found."
        
        # LLM
        analysis = llm_service.analyze_clause(clause, law_context)
        
        if analysis.get("risk_found"):
            # Add clause snippet to the result for context
            analysis["clause_snippet"] = clause
            results.append(analysis)
            
    # If no risks found but we analyzed stuff, maybe return a "Clean" status? 
    # Or if we found nothing relevant to analyze?
    if not results and not target_indices:
        return {"risks": [], "message": "No relevant lease clauses found to analyze."}
        
    return {"risks": results}

@router.post("/generate-letter")
async def generate_letter(request: LetterRequest):
    print("[INFO] Generating letter...")
    letter = llm_service.generate_letter(request.risk_details)
    return {"letter": letter}
