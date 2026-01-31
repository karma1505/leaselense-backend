import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "LeaseLense Backend"
    API_V1_STR: str = "/api/v1"
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY")
    FASTROUTER_API_KEY: str = os.getenv("FASTROUTER_API_KEY")
    CHROMA_DB_DIR: str = os.path.join(os.getcwd(), "chroma_db")

settings = Settings()
