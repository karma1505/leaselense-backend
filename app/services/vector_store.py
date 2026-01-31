import chromadb
from chromadb.utils import embedding_functions
from chromadb.config import Settings as ChromaSettings
from app.core.config import settings
import logging
import os

logger = logging.getLogger(__name__)

class VectorStoreService:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=str(settings.CHROMA_DB_DIR))
        
        # Ensure we use the same embedding function as the seeder
        gemini_ef = embedding_functions.GoogleGenerativeAiEmbeddingFunction(
            api_key=settings.GEMINI_API_KEY
        )
        
        self.collection = self.client.get_or_create_collection(
            name="legal_knowledge",
            embedding_function=gemini_ef
        )

    def add_law_chunks(self, chunks: list[dict]):
        ids = [f"{chunk['law']}_{chunk['section']}_{i}" for i, chunk in enumerate(chunks)]
        documents = [chunk['text'] for chunk in chunks]
        metadatas = [{k: v for k, v in chunk.items() if k != 'text'} for chunk in chunks]
        
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        logger.info(f"Added {len(documents)} chunks to the vector store.")

    def query_similar(self, query: str, n_results: int = 3):
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results

vector_store = VectorStoreService()
