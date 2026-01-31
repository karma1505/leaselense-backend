import asyncio
import re
from app.services.vector_store import vector_store

TEXT_PATH = "../frontend/public/MTA_full_text.txt"

def parse_mta_text(text: str):
    """
    Splits the full text into sections based on the pattern "1. Title", "2. Title", etc.
    This is a heuristic parser tailored for the MTA structure found in the logs.
    """
    chunks = []
    lines = text.split('\n')
    
    current_section = None
    current_topic = None
    current_text = []
    
    # Regex to find "21. Eviction and recovery..." starting a line
    # Matches "4. ", "21. " etc at start of line
    section_pattern = re.compile(r'^(\d+)\.\s+(.+)$')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Skip page numbers and headers if possible
        if line.startswith("Page ") or line.startswith("CHAPTER ") or line == "THE MODEL TENANCY ACT, 2021":
            continue

        match = section_pattern.match(line)
        if match:
            # If we were building a section, save it
            if current_section:
                chunks.append({
                    "law": "Model Tenancy Act 2021",
                    "section": f"Section {current_section}",
                    "topic": current_topic,
                    "text": "\n".join(current_text).strip()
                })
            
            # Start new section
            current_section = match.group(1)
            current_topic = match.group(2).strip()
            current_text = [line] # Include the title in the text for context
        else:
            if current_section:
                current_text.append(line)
                
    # Append the last section
    if current_section:
         chunks.append({
            "law": "Model Tenancy Act 2021",
            "section": f"Section {current_section}",
            "topic": current_topic,
            "text": "\n".join(current_text).strip()
        })
        
    return chunks

async def seed_full_mta():
    print(f"[INFO] Parsing full law text from {TEXT_PATH}...")
    
    try:
        with open(TEXT_PATH, "r", encoding="utf-8") as f:
            full_text = f.read()
            
        chunks = parse_mta_text(full_text)
        print(f"[INFO] Parsed {len(chunks)} sections/chunks.")
        
        if not chunks:
            print("[ERROR] No chunks found! Regex might need tuning.")
            return

        print(f"[INFO] Ingesting {len(chunks)} chunks into ChromaDB...")
        vector_store.add_law_chunks(chunks)
        print("[SUCCESS] Full MTA Ingestion complete!")
        
        # Validation Query
        test_q = "security deposit return limit"
        print(f"\n[TEST] Querying: '{test_q}'")
        results = vector_store.query_similar(test_q)
        print(f"[RESULT] Found {len(results['documents'][0])} matches.")
        for i, doc in enumerate(results['documents'][0]):
            meta = results['metadatas'][0][i]
            print(f" - [{meta['section']}]: {doc[:100]}...")
            
    except Exception as e:
        print(f"[ERROR] Failed: {e}")

if __name__ == "__main__":
    asyncio.run(seed_full_mta())
