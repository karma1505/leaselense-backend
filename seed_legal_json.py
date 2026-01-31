import json
import time
import os
import sys
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions
from app.core.config import settings

# Configuration
DATA_SOURCES_DIR = Path("data_sources")
COLLECTION_NAME = "legal_knowledge"
BATCH_SIZE = 5
DELAY_SECONDS = 20  # Respect Gemini Free Tier limits (drastic increase to handle 429)

# Files to ingest in order
TARGET_FILES = [
    "mrca.json",
    "registration_act_1908.json",
    "transfer_of_property_act_1882.json"
]

def get_db_client():
    return chromadb.PersistentClient(path=str(settings.CHROMA_DB_DIR))

def reset_collection(client, collection_name):
    print(f"[INFO] 🔄 Resetting collection '{collection_name}' for fresh ingestion...")
    try:
        client.delete_collection(collection_name)
        print(f"[SUCCESS] Deleted existing collection.")
    except Exception:
        print(f"[INFO] Collection did not exist, creating new.")
    
    # Embedding Function (Local)
    # Using 'all-MiniLM-L6-v2' which is lightweight and fast.
    print(f"[INFO] 🧠 Loading local embedding model (sentence-transformers)...")
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    
    return client.create_collection(name=collection_name, embedding_function=ef)

def ingest_file(collection, filename):
    filepath = DATA_SOURCES_DIR / filename
    if not filepath.exists():
        print(f"[ERROR] ❌ File not found: {filename}")
        return False

    print(f"\n[INFO] 🚀 Starting ingestion for: {filename}")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        source_name = data.get("metadata", {}).get("act_name", filename)
        sections = data.get("sections", [])
        
        if not sections:
            print(f"[WARNING] ⚠️ No sections found in {filename}")
            return True # Not a failure, just empty
            
        print(f"[INFO] Found {len(sections)} sections in {source_name}")
        
        chunks = []
        for sec in sections:
            # Construct meaningful content and robust ID
            content = f"{sec['title']}: {sec['content']}"
            
            # Sanitize section number for ID (remove spaces/special chars if needed, but keeping simple is ok usually)
            # ID format: "ActName_SectionNumber"
            safe_act = source_name.replace(" ", "_")
            safe_sec = str(sec['section_number']).replace(" ", "")
            
            # Check for duplicates in JSON itself? Assuming JSON is clean.
            
            metadata = {
                "source": source_name,
                "section": f"Section {sec['section_number']}",
                "category": sec.get("category", "General"),
                "relevance": sec.get("relevance", "")
            }
            chunks.append({
                "text": content, 
                "metadata": metadata, 
                "id": f"{safe_act}_{safe_sec}"
            })
            
        # Batch Ingestion
        total_chunks = len(chunks)
        for i in range(0, total_chunks, BATCH_SIZE):
            batch = chunks[i : i + BATCH_SIZE]
            print(f"  -> ⏳ Ingesting batch {i//BATCH_SIZE + 1}/{(total_chunks + BATCH_SIZE - 1)//BATCH_SIZE}...")
            
            collection.add(
                documents=[c["text"] for c in batch],
                metadatas=[c["metadata"] for c in batch],
                ids=[c["id"] for c in batch]
            )
            time.sleep(DELAY_SECONDS)
            
        print(f"[PASS] ✅ Successfully ingested {filename}")
        return True
        
    except Exception as e:
        print(f"[FAIL] ❌ Failed to ingest {filename}: {str(e)}")
        return False

def verify_file(collection, filename):
    filepath = DATA_SOURCES_DIR / filename
    if not filepath.exists():
        return False
        
    print(f"\n[INFO] 🔍 Verifying data for: {filename}")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        source_name = data.get("metadata", {}).get("act_name", filename)
        sections = data.get("sections", [])
        
        # Verify count
        # We query by source name in metadata
        results = collection.get(where={"source": source_name})
        db_count = len(results['ids'])
        json_count = len(sections)
        
        if db_count == json_count:
            print(f"[PASS] ✅ Count Matched: {db_count}/{json_count}")
        else:
            print(f"[FAIL] ❌ Count Mismatch: DB has {db_count}, JSON has {json_count}")
            return False
            
        # Verify IDs (deeper check)
        missing = []
        for sec in sections:
            safe_act = source_name.replace(" ", "_")
            safe_sec = str(sec['section_number']).replace(" ", "")
            expected_id = f"{safe_act}_{safe_sec}"
            
            if expected_id not in results['ids']:
                missing.append(expected_id)
        
        if missing:
            print(f"[FAIL] ❌ Missing IDs in DB: {missing}")
            return False
        else:
            print(f"[PASS] ✅ All {json_count} sections verify 100%")
            return True

    except Exception as e:
        print(f"[FAIL] ❌ Verification error for {filename}: {e}")
        return False

def main():
    print("=== ⚖️  LeaseLense Legal Data Ingestion  ⚖️ ===")
    
    # 1. Init & Reset DB
    client = get_db_client()
    collection = reset_collection(client, COLLECTION_NAME)
    
    results = {}
    
    # 2. Ingest
    print("\n--- Phase 1: Ingestion ---")
    for filename in TARGET_FILES:
        success = ingest_file(collection, filename)
        results[filename] = {"ingest": success}
        # Atomic: catch exception inside ingest_file ensures we continue, 
        # but ingest_file returning False also signals failure.
    
    # 3. Verify
    print("\n--- Phase 2: Verification ---")
    for filename in TARGET_FILES:
        if results[filename]["ingest"]:
            verified = verify_file(collection, filename)
            results[filename]["verify"] = verified
        else:
             results[filename]["verify"] = False
             print(f"[SKIP] ⏭️  Skipping verification for {filename} due to ingestion failure.")

    # 4. Summary
    print("\n=== 📊 Final Summary ===")
    all_pass = True
    for fname, res in results.items():
        ingest_status = "✅ PASS" if res["ingest"] else "❌ FAIL"
        verify_status = "✅ PASS" if res.get("verify") else "❌ FAIL"
        print(f"{fname}: Ingest [{ingest_status}] | Verify [{verify_status}]")
        if not (res["ingest"] and res.get("verify")):
            all_pass = False
            
    if all_pass:
        print("\n🎉 All systems go! Legal DB is seeded and verified.")
        sys.exit(0)
    else:
        print("\n⚠️  Some files failed. Check logs.")
        sys.exit(1)

if __name__ == "__main__":
    main()
