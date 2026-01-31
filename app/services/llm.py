import google.generativeai as genai
from app.core.config import settings
import json

class LLMService:
    def __init__(self):
        if not settings.GEMINI_API_KEY:
            print("[LLM ERROR] GEMINI_API_KEY is missing in settings!")
        else:
            print(f"[LLM INFO] Gemini API Key loaded: {settings.GEMINI_API_KEY[:4]}...{settings.GEMINI_API_KEY[-4:]}")
            
        genai.configure(api_key=settings.GEMINI_API_KEY)
        # Flash for speed/cost (Analysis), Pro for reasoning (Letters)
        self.analysis_model = genai.GenerativeModel('gemini-flash-latest')
        self.writing_model = genai.GenerativeModel('gemini-flash-latest')

    def analyze_clause(self, clause_text: str, law_context: str) -> dict:
        prompt = f"""
        You are an expert legal AI helper for LeaseLense. Analyze the following lease clause against the provided legal context (Laws like MRCA 1999, Registration Act 1908, TPA 1882).

        Clause: "{clause_text}"

        Legal Context: "{law_context}"

        Task: Determine if there is a risk or violation.
        
        ### IGNORE STANDARD PRACTICES
        You are analyzing a residential lease in India (Maharashtra). Do NOT flag the following standard market practices as risks:
        1. "Interest-Free Security Deposit": This is standard practice in India. Do not flag it as a financial loss.
        2. "Licensor pays Municipal Taxes/Maintenance": This is the legal duty of the landlord. It is a PROTECTION for the tenant, not a risk. Do not flag it.
        3. "11-Month Term": This is standard for Leave and License agreements.
        4. "Deduction for Arrears/Damages": It is standard to deduct unpaid bills from the deposit.

        ONLY flag clauses that violate the 'Maharashtra Rent Control Act' or create unfair/unreasonable liabilities for the Tenant (e.g., huge penalties, eviction without notice, invasion of privacy).

        Return ONLY valid JSON with this structure:
        {{
            "risk_found": boolean,
            "risk_type": string (e.g., "Security Deposit", "Notice Period", "Maintenance", "Rent Increase"),
            "explanation": string (concise logic citing the law),
            "confidence": string ("High", "Medium", "Low")
        }}
        """
        
        try:
            response = self.analysis_model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
            return json.loads(response.text)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"[LLM ERROR] Analysis failed details: {str(e)}")
            return {
                "risk_found": False,
                "risk_type": "Error",
                "explanation": "AI analysis failed. Please verify API key.",
                "confidence": "Low"
            }

    def generate_letter(self, risk_details: dict) -> str:
        prompt = f"""
        Draft a polite but firm negotiation email to a landlord based on this legal risk:
        {json.dumps(risk_details, indent=2)}
        
        The email should:
        1. Cite the specific issue.
        2. Reference the Model Tenancy Act principles implies by the risk (if applicable).
        3. Propose a specific correction.
        4. Keep the relationship professional.
        """
        
        try:
            response = self.writing_model.generate_content(prompt)
            return response.text
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"[LLM ERROR] Letter generation failed: {str(e)}")
            return "Error generating letter. Please try again."

llm_service = LLMService()
