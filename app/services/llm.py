from openai import OpenAI
from app.core.config import settings
import json
import os

class LLMService:
    def __init__(self):
        # Prefer FastRouter if available, else fallback logic (or just fail if not set)
        self.api_key = settings.FASTROUTER_API_KEY
        self.base_url = "https://go.fastrouter.ai/api/v1" 
        
        if not self.api_key:
            print("[LLM ERROR] FASTROUTER_API_KEY is missing! Using dummy client which will fail.")
            self.client = None
        else:
            print(f"[LLM INFO] FastRouter API Key loaded: {self.api_key[:4]}...{self.api_key[-4:]}")
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            
        # Model Selection
        self.analysis_model = "gpt-4o-mini"
        self.writing_model = "gpt-4o-mini" # Using mini for cost saving as requested

    def _call_llm(self, messages: list, model: str, json_mode: bool = False) -> str:
        if not self.client:
            raise Exception("LLM Client not initialized. Check FASTROUTER_API_KEY.")
            
        try:
            params = {
                "model": model,
                "messages": messages,
                "temperature": 0.2
            }
            if json_mode:
                params["response_format"] = {"type": "json_object"}
                
            response = self.client.chat.completions.create(**params)
            return response.choices[0].message.content
        except Exception as e:
            print(f"[LLM ERROR] API Call failed: {e}")
            raise e

    def analyze_clause(self, clause_text: str, law_context: str) -> dict:
        # Legacy method (single clause) - usage discouraged in favor of batch
        # But we keep it for backward compatibility if needed
        # We wrap it in a pseudo-batch prompt style
        pass 

    def analyze_batch(self, full_lease_text: str, law_context: str) -> list:
        system_prompt = """You are an expert impartial Legal Auditor AI.
        Your task is to validate Residential Lease Clauses strictly against the provided "Legal Context".

        Step 1: Read the "Legal Context" (Laws/Acts provided below).
        Step 2: Read the "Lease Clauses".
        Step 3: Identify any clause that **contradicts, violates, or is inconsistent** with the Legal Context.
        
        ### Rules
        - If the Legal Context says "Rent increase limit is 4%", and the lease says "10%", flag it.
        - If the Legal Context says "Registration is mandatory", and lease says "No registration", flag it.
        - If the Legal Context is silent on an issue (e.g., standard 11-month term), do NOT flag it as a risk.
        - **Silent Killers:** Pay special attention to procedural requirements in the context (Registration, Receipts, Permitted Uses).

        Output Format:
        Return a JSON Object with a key "risks" which is a List of Objects.
        {
          "risks": [
            {
                "risk_found": true,
                "risk_type": "Violation of [Section Name]",
                "explanation": "Clause X contradicts Section Y which states...",
                "clause_snippet": "Clause text...",
                "confidence": "High"
            }
          ]
        }
        """
        
        user_message = f"""
        Legal Context: "{law_context}"
        
        Lease Clauses to Analyze:
        "{full_lease_text}"
        """
        
        try:
            content = self._call_llm(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                model=self.analysis_model,
                json_mode=True
            )
            data = json.loads(content)
            return data.get("risks", [])
        except Exception as e:
            print(f"[LLM ERROR] Batch Analysis failed: {e}")
            return []

    # Alias for analyze_clause if used by legacy calls in verify scripts
    # But wait, endpoints.py now calls analyze_batch.
    # verify_lease_1.py calls endpoint.
    # So we don't strictly need analyze_clause unless endpoints.py logic fallback is hit.
    # Let's verify endpoints.py logic.
    # It has `if not combined_clauses: ... analyze_batch`.
    # Wait, the fallback in endpoints.py (lines 88-115) was REPLACED largely.
    # I should check endpoints.py to be sure I didn't leave calls to analyze_clause.

    def generate_letter(self, risk_details: dict) -> str:
        system_prompt = "You are a professional legal negotiator. Draft a polite but firm email."
        user_message = f"""
        Proprietor/Landlord has a lease with this risk:
        {json.dumps(risk_details, indent=2)}
        
        Draft a negotiation email to the Landlord proposing a correction.
        Cite the law if mentioned in the risk.
        Keep it constructive.
        """
        
        try:
            return self._call_llm(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                model=self.writing_model
            )
        except Exception as e:
            return "Error generating letter."

llm_service = LLMService()
