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
    keywords = ["deposit", "security", "refund", "termination", "notice", "repair", "maintenance", "increase", "rent", "evic", "utilit", "electricity", "water", "registrat", "lock-in", "penal", "damages", "enter", "entry", "possession"]
    
    for i, p in enumerate(paragraphs):
        if any(k in p.lower() for k in keywords):
            idx_to_analyze.append(i)
            
    # Limit to specific relevant chunks to save time/quota, or analyze all relevant ones?
    # Let's take up to 20 relevant chunks (covering most standard leases)
    target_indices = idx_to_analyze[:20]
    
    # --- OPTIMIZATION: BATCH PROCESSING ---
    # Instead of calling LLM for each chunk (burning quota), we will:
    # 1. Gather RAG context for all chunks (Free).
    # 2. Send ONE prompt with all clauses and merged context.
    
    combined_clauses = []
    combined_laws = set()
    
    for i in target_indices:
        clause = paragraphs[i]
        # RAG Search (Local & Free)
        relevant_laws_result = vector_store.query_similar(clause, n_results=2)
        combined_clauses.append(f"Clause {i+1}: {clause}")
        if relevant_laws_result and relevant_laws_result['documents']:
            for doc in relevant_laws_result['documents'][0]:
                combined_laws.add(doc)
            
    if not combined_clauses:
        return {"risks": [], "message": "No relevant lease clauses found to analyze."}
        
    # Prepare Single Request
    full_lease_text = "\n\n".join(combined_clauses)
    merged_law_context = "\n\n".join(list(combined_laws))
    
    print(f"[INFO] Sending BATCH analysis (1 request) for {len(combined_clauses)} clauses...")
    
    # Call LLM Once
    # We need to update llm.analyze_clause or create a new method analyze_full_lease
    # For now, let's reuse analyze_clause but expect a list of risks in the explanation?
    # Actually, analyze_clause returns a single dict {risk_found, risk_type...}.
    # We should update LLM prompt to return a LIST of risks.
    
    analysis = llm_service.analyze_batch(full_lease_text, merged_law_context)
    
    # Analysis is now a list of risks
    return {"risks": analysis}

@router.post("/generate-letter")
async def generate_letter(request: LetterRequest):
    print("[INFO] Generating letter...")
    letter = llm_service.generate_letter(request.risk_details)
    return {"letter": letter}
