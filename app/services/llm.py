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
        system_prompt = """You are an expert Indian Legal Aid AI.
        Your task is to analyze Residential Lease Clauses against the provided Legal Context (Maharashtra Rent Control Act / Transfer of Property Act).
        
        ### IGNORE STANDARD PRACTICES (Green Flags)
        Do NOT flag:
        1. Interest-Free Security Deposit.
        2. Licensor paying Taxes.
        3. 11-Month Term.
        4. Deduction for Arrears/Damages.
        5. Double Rent for overstaying (Mesne Profits).

        ### FLAG THESE RISKS (Red Flags)
        1. Rent Increase > 4% (MRCA Sec 11).
        2. Entry without notice (TPA Sec 108).
        3. Forced Eviction (MRCA Sec 16).
        4. Tenant paying for Structural Repairs (TPA Sec 108).
        5. Cutting Utilities (MRCA Sec 29).
        6. Unreasonable Lock-in (Unilateral or > Term).
        7. **Non-Registration**: Clause forbidding registration (Void lease under Registration Act Sec 17).
        8. **Tax Evasion**: Clause denying rent receipts (MRCA Sec 31 Violation).
        9. **Illegal/Hazardous Use**: Clause permitting industrial/dangerous use in residential zone.

        Output Format:
        Return a JSON Object with a key "risks" which is a List of Objects.
        {
          "risks": [
            {
                "risk_found": true,
                "risk_type": "Rent Increase",
                "explanation": "Clause X mentions 10% increase which violates limit of 4%.",
                "clause_snippet": "Clause 3: ... increase by 10%...",
                "citation": "MRCA Section 11",
                "confidence": "High"
            }
          ]
        }
        If no risks, return {"risks": []}.
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

    def translate_content(self, data: dict, target_language: str) -> dict:
        system_prompt = f"""You are a legal translator expert in Indian Law.
        Translate the values in the provided JSON to {target_language}.
        
        RULES:
        1. Keep all JSON keys exactly the same.
        2. Translate 'explanation', 'risk_type', 'citation'.
        3. Do NOT translate 'risk_found', 'confidence' (Keep confidence as High/Medium/Low but you can append translation in brackets if needed, e.g. "High (उuch)").
        4. For 'clause_snippet', keep the original English text but provide a translation in brackets.
        5. Ensure legal terms are translated accurately for the context (Maharashtra Rent Control, etc).
        
        Input JSON:
        {json.dumps(data)}
        """
        
        try:
            content = self._call_llm(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Translate the JSON."}
                ],
                model=self.writing_model,
                json_mode=True
            )
            return json.loads(content)
        except Exception as e:
            print(f"[LLM ERROR] Translation failed: {e}")
            return data # Fallback to original

llm_service = LLMService()
