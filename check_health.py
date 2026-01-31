import asyncio
import httpx
import sys
import os
from chromadb import PersistentClient
from app.core.config import settings

# Configuration
FRONTEND_URL = "http://localhost:3000"
BACKEND_URL = "http://localhost:8000"
DB_PATH = settings.CHROMA_DB_DIR

def check_db():
    print(f"[INFO] Checking Vector DB at {DB_PATH}...")
    try:
        if not os.path.exists(DB_PATH):
            print(f"[WARNING] ChromaDB directory not found at {DB_PATH}. It might be created on first write.")
        
        client = PersistentClient(path=DB_PATH)
        heartbeat = client.heartbeat()
        print(f"[SUCCESS] ChromaDB is responsive (heartbeat: {heartbeat})")
        return True
    except Exception as e:
        print(f"[ERROR] ChromaDB Check Failed: {e}")
        return False

async def check_service(name: str, url: str):
    print(f"[INFO] Checking {name} at {url}...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=5.0)
            if response.status_code == 200:
                print(f"[SUCCESS] {name} is Online ({response.status_code})")
                return True
            else:
                print(f"[WARNING] {name} returned status {response.status_code}")
                return False
    except httpx.ConnectError:
        print(f"[ERROR] {name} Connection Refused. Is the server running?")
        return False
    except Exception as e:
        print(f"[ERROR] {name} Check Failed: {e}")
        return False

async def main():
    print("=== LeaseLense System Health Check ===")
    
    # 1. Check DB (Local)
    db_ok = check_db()
    
    # 2. Check Backend
    backend_ok = await check_service("FastAPI Backend", BACKEND_URL)
    
    # 3. Check Frontend
    frontend_ok = await check_service("Next.js Frontend", FRONTEND_URL)
    
    print("\n=== Summary ===")
    if db_ok and backend_ok and frontend_ok:
        print("✅ All systems operational.")
        sys.exit(0)
    else:
        print("❌ Some systems are down or experiencing issues.")
        sys.exit(1)

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
