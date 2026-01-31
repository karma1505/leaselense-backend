import os
import shutil
from pathlib import Path
import re
from typing import List, Dict

import chromadb
from chromadb.utils import embedding_functions
from docling.document_converter import DocumentConverter

# Configuration
FRONTEND_PUBLIC_DIR = Path("../frontend/public")
CHROMA_DB_DIR = Path("chroma_db")
COLLECTION_NAME = "legal_knowledge"

# Files to ingest
TARGET_FILES = [
    "MRCA_1999.pdf",
    "Registration_Act_1908.pdf",
    "Transfer_Of_Property_Act.pdf"
]

def clean_text(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip()

def chunk_by_sections(text: str, source_doc: str) -> List[Dict]:
    """
    Splits text into chunks based on "Section X" patterns.
    This is a heuristic and might need tuning based on exact PDF content.
    """
    chunks = []
    
    # Regex to find "Section <number>"
    # We look for "Section" followed by digits, capturing the number and the following text
    # This splits the document by "Section ...", keeping the delimiter
    # Note: nuances in PDF extraction might make this tricky (e.g. headers).
    # We'll use a simple split and attach metadata.
    
    # Simpler approach: Split by "Section "
    parts = re.split(r'(Section\s+\d+)', text)
    
    current_section_title = "Preamble/Intro"
    
    # parts[0] is text before first section
    if parts[0].strip():
        chunks.append({
            "text": clean_text(parts[0]),
            "metadata": {"source": source_doc, "section": "Intro"}
        })
        
    # Iterate over the rest. split keeps the delimiter, so:
    # parts[1] is "Section 1", parts[2] is body of section 1
    # parts[3] is "Section 2", parts[4] is body of section 2
    for i in range(1, len(parts), 2):
        section_header = parts[i].strip()
        section_body = parts[i+1] if i+1 < len(parts) else ""
        
        full_text = f"{section_header}: {section_body}"
        
        # Further chunking if too large? For now, keep section-level granularity.
        # Max context window is usually large enough for one section.
        
        chunks.append({
            "text": clean_text(full_text),
            "metadata": {
                "source": source_doc,
                "section": section_header
            }
        })
        
    return chunks

def seed_db():
    print(f"[INFO] Initializing ChromaDB at {CHROMA_DB_DIR}...")
    client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
    
    # Reset/Recreate collection
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"[INFO] Deleted existing collection '{COLLECTION_NAME}'")
    except Exception as e:
        print(f"[INFO] Collection '{COLLECTION_NAME}' did not exist or could not be deleted: {e}")
        
    # Use OpenAI Embeddings (assuming env var is set, or default to generic if not)
    # Check if OPENAI_API_KEY is set
    if not os.getenv("OPENAI_API_KEY"):
        print("[WARNING] OPENAI_API_KEY not found. Using default sentence-transformers (might necessitate local download).")
        # embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    
    # Actually, let's use the one from config or just rely on default for now if key exists.
    # Ideally we use the same embedding function as the app.
    # For hackathon simplicity, let's rely on 'text-embedding-3-small' if possible, 
    # but chromadb default is different.
    # Let's explicitly use OpenAI if key present.
    
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
                api_key=os.environ.get("OPENAI_API_KEY"),
                model_name="text-embedding-3-small"
            )
    
    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=openai_ef
    )
    
    converter = DocumentConverter()
    
    for filename in TARGET_FILES:
        filepath = FRONTEND_PUBLIC_DIR / filename
        if not filepath.exists():
            print(f"[ERROR] File not found: {filepath}")
            continue
            
        print(f"[INFO] Processing {filename} with Docling...")
        try:
            result = converter.convert(filepath)
            # Export to markdown to keep some structure, distinct from raw text
            md_content = result.document.export_to_markdown()
            
            # Chunk it
            chunks = chunk_by_sections(md_content, filename)
            print(f"[INFO] Extracted {len(chunks)} sections from {filename}")
            
            if not chunks:
                continue
                
            # Add to DB
            collection.add(
                documents=[c["text"] for c in chunks],
                metadatas=[c["metadata"] for c in chunks],
                ids=[f"{filename}_{i}" for i in range(len(chunks))]
            )
            
        except Exception as e:
            print(f"[ERROR] Failed to process {filename}: {e}")

    print(f"[SUCCESS] Ingestion complete. Collection '{COLLECTION_NAME}' now has {collection.count()} documents.")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv() # Load .env
    seed_db()
