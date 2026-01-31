import asyncio
from app.services.vector_store import vector_store

# Key Sections from Model Tenancy Act, 2021
# We focus on the most common risks for the hackathon demo.

MTA_CORPUS = [
    {
        "law": "Model Tenancy Act 2021",
        "section": "Section 11(1)",
        "topic": "Security Deposit",
        "text": "The security deposit to be paid by the tenant in advance shall be as determined by mutual agreement between the landlord and the tenant, subject to a maximum of two months' rent in case of residential premises."
    },
    {
        "law": "Model Tenancy Act 2021",
        "section": "Section 11(2)",
        "topic": "Security Deposit",
        "text": "The security deposit shall be refunded to the tenant without interest within one month of the termination of the tenancy or vacation of the premises by the tenant, after making due deductions of any liability of the tenant."
    },
    {
        "law": "Model Tenancy Act 2021",
        "section": "Section 8",
        "topic": "Rent Increase",
        "text": "The rent may be increased according to the terms of the tenancy agreement. If no such term exists, the landlord must give three months' notice in writing to the tenant before increasing the rent."
    },
    {
        "law": "Model Tenancy Act 2021",
        "section": "Section 15",
        "topic": "Maintenance",
        "text": "The landlord and tenant shall be responsible for the repair and maintenance of the premises as agreed in the tenancy agreement. However, structural repairs are typically the responsibility of the landlord unless caused by the tenant's damage."
    },
    {
        "law": "Model Tenancy Act 2021",
        "section": "Section 21",
        "topic": "Eviction",
        "text": "A tenant shall not be evicted during the continuance of the tenancy agreement except in accordance with the provisions of this Act (e.g., non-payment of rent for two consecutive months, misuse of premises)."
    },
    {
        "law": "Model Tenancy Act 2021",
        "section": "Section 9",
        "topic": "Access",
        "text": "The landlord may enter the premises for inspection or repairs only after giving twenty-four hours' notice in writing or through electronic medium to the tenant."
    }
]

async def seed_db():
    print(f"[INFO] Seeding {len(MTA_CORPUS)} law chunks into ChromaDB...")
    try:
        # The vector_store service is synchronous (ChromaClient), so we call it directly
        vector_store.add_law_chunks(MTA_CORPUS)
        print("[SUCCESS] Ingestion complete! The Brain is ready.")
        
        # Verify
        print("\n[TEST] Verifying with a query: 'security deposit limit'")
        results = vector_store.query_similar("maximum security deposit limit")
        print(f"[RESULT] Found {len(results['documents'][0])} matches.")
        for doc in results['documents'][0]:
            print(f" - {doc[:100]}...")
            
    except Exception as e:
        print(f"[ERROR] Failed to seed DB: {e}")

if __name__ == "__main__":
    asyncio.run(seed_db())
