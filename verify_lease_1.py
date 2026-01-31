import httpx
import time
from pathlib import Path

BASE_URL = "http://localhost:8000/api/v1/analyze"
LEASE_PATH = "demo_leases/Demo_Lease_1_Compliant.md"

def verify_lease():
    print(f"=== 🔍 Verifying {LEASE_PATH} ===")
    
    try:
        with open(LEASE_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
            
        print(f"[INFO] Sending {len(content)} chars to AI...")
        start = time.time()
        
        response = httpx.post(BASE_URL, json={"clause_text": content}, timeout=120.0)
        duration = time.time() - start
        
        if response.status_code != 200:
            print(f"[ERROR] Request failed: {response.text}")
            return

        data = response.json()
        print(f"[SUCCESS] Analysis received in {duration:.2f}s")
        
        risks = data.get("risks", [])
        print(f"\n[REPORT] Risks Found: {len(risks)}")
        
        for i, r in enumerate(risks, 1):
            print(f"{i}. Type: {r.get('risk_type')} | Found: {r.get('risk_found')}")
            print(f"   Expl: {r.get('explanation')[:100]}...")
            
        if not risks:
            print("\n✅ PASSED: No risks found as expected for a compliant lease.")
        else:
             print("\n⚠️ UNEXPECTED: Risks were found in a compliant lease.")

    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    verify_lease()
