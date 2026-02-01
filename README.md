# LeaseLensAI Engine 🧠⚡  
> **The Intelligent Core of LeaseLensAI.**  
> *Processing legal complexity into simple, actionable insights.*

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-High_Performance-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![OpenAI](https://img.shields.io/badge/AI-GPT--4o--mini-412991?style=flat-square&logo=openai)](https://openai.com/)
[![ChromaDB](https://img.shields.io/badge/Vector_DB-Chroma-orange?style=flat-square)](https://www.trychroma.com/)

---

## ⚙️ Overview

This is the **Backend API** for LeaseLensAI. It handles the heavy lifting of legal document analysis. It ingests PDF lease agreements, chunks them into semantic sections, and uses a **RAG (Retrieval-Augmented Generation)** pipeline to evaluate them against Indian Rental Laws.

It exposes a RESTful API consumed by the frontend to provide real-time risk scores and drafts.

### 🧠 The Intelligence Stack
1.  **Ingestion Layer**: Advanced PDF parsing & OCR powered by **Docling** to handle complex scanned leases and layouts.
2.  **Legal Knowledge Base**: A vector database (ChromaDB) containing the **Model Tenancy Act (2021)** and **Maharashtra Rent Control Act**.
3.  **Reasoning Engine**: Uses **OpenAI GPT-4o-mini** (via FastRouter) to "think" like a lawyer. It doesn't just match keywords; it understands *implications*.
4.  **Translation Layer**: On-the-fly localization of complex legal advice into native Hindi and Marathi.

---

## 🏗️ Architecture

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **API Server** | **FastAPI** | High-performance async REST API. |
| **LLM** | **GPT-4o-mini (via FastRouter)** | The "Brain" for analyzing risks and drafting text. |
| **OCR** | **Docling** | High-fidelity document parsing. |
| **Vector DB** | **ChromaDB** | Stores legal embeddings for context retrieval. |
| **Embeddings** | **HuggingFace** | Creates vector representations of checking clauses. |
| **Tunneling** | **Ngrok** | Exposes local host to the public Vercel frontend. |

---

## 🔌 Key Endpoints

- `POST /analyze`: Upload a PDF lease. Returns a JSON object with a Risk Score and list of "Silent Killers".
- `POST /translate`: Converts the analysis report into a target language (Hindi/Marathi).
- `POST /generate-letter`: Drafts a negotiation email or WhatsApp message based on the found risks.

---

## 🚀 Getting Started

To run the engine locally:

1. **Set up Environment**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set API Keys**
   Create a `.env` file and add your key:
   ```env
   FAST_ROUTER_API_KEY=your_key_here
   ```

4. **Ignition**
   ```bash
   uvicorn main:app --reload --port 8000
   ```

5. **Expose to World (Optional)**
   ```bash
   ngrok http 8000
   ```

---

## ❤️ Credits
Made with ❤️ in **AI-Boomi, Pune**.
