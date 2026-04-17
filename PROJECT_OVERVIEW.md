# YojanaIQ Project Overview

YojanaIQ is an intelligent Retrieval-Augmented Generation (RAG) system designed to help citizens of Andhra Pradesh discover and understand government welfare schemes. It combines a deterministic rule-based eligibility engine with a sophisticated hybrid retrieval pipeline (BM25 + ChromaDB + Reranking) to provide grounded, multi-lingual answers.

---

## 🏗️ Architecture & Workflow

### 1. User Engagement (Frontends)
*   **Web Portal (React):** A premium, dark-themed UI built with Vite and TailwindCSS that walks users through a guided profile setup.
*   **Telegram Bot (Python):** An interactive bot that uses conversation handlers to collect user data and answer queries via chat.

### 2. Eligibility Engine (`rule_filter.py`)
*   **Deterministic Logic:** Unlike standard LLMs which might hallucinate eligibility, YojanaIQ uses a hard-coded rule engine. 
*   **Input:** User profile (Age, Gender, Caste, Religion, Occupation, Income, etc.).
*   **Process:** Maps the profile to implicit "flags" (e.g., a "female" student under 18 gets a `school_student` flag) and matches them against `data/schemes.json`.
*   **Output:** Lists of `matched` and `rejected` schemes with specific reasons for rejection.

### 3. Core RAG Pipeline (`rag.py` & `retrieval.py`)
When a user asks a question after matching:
1.  **Hybrid Retrieval:** `retrieval.py` uses **BM25** (keyword) and **ChromaDB** (semantic) to find relevant chunks from the parsed scheme documentation. Results are fused using **Reciprocal Rank Fusion (RRF)**.
2.  **Reranking:** `reranker.py` uses a **Cross-Encoder** (`ms-marco-MiniLM-L-6-v2`) to precisely rank the top chunks based on the query.
3.  **Prompt Engineering:** `rag.py` constructs a "System-User" prompt that includes:
    *   Verified User Profile (Ground Truth).
    *   Confirmed Eligible Schemes (Authoritative).
    *   Retrieved Context Chunks (Only Source of Truth).
    *   Query-Specific Instructions (for Eligibility, How-to-Apply, Documents, or Payment Status).
4.  **Generation:** Queries **Groq (Llama 3.1 8B/70B)** with a low temperature (0.1) for factual accuracy.
5.  **Faithfulness Check:** Performs a cosine similarity check between the answer and the context to flag potential hallucinations.

---

## 📁 File Directory & Responsibilities

### Backend / Core
- **`main.py`**: FastAPI server hosting `/api/match` and `/api/chat` endpoints.
- **`rag.py`**: The "brain" of the RAG system. Handles prompt construction, LLM calls, and faithfulness checks.
- **`retrieval.py`**: Implements hybrid search logic (BM25 + Semantic) and RRF fusion.
- **`rule_filter.py`**: The deterministic eligibility bot that prevents LLM hallucinations regarding local policy.
- **`reranker.py`**: Refines retrieval results using a transformer-based cross-encoder.
- **`bot.py`**: Orchestrates the Telegram Bot experience.
- **`embed.py` / `embed_bm25.py`**: Scripts to pre-process `data/schemes.pdf` and create the vector database and keyword index.

### Frontend
- **`frontend/src/App.jsx`**: Main React component managing conversation state, profile collection, and multi-lingual UI transitions.
- **`frontend/src/index.css`**: Design tokens and layout styling.

### Data
- **`data/schemes.json`**: Structured metadata for the rule engine (min_age, max_income, etc.).
- **`data/schemes.pdf`**: The raw source text for all schemes.
- **`chroma_db/`**: Persistent vector database containing scheme embeddings.

---

## 🔑 Important Code Snippets

### Rule Filtering (`rule_filter.py`)
```python
def rule_filter(user_profile):
    # Matches physical profile against scheme attributes
    for scheme in schemes:
        if u_age < scheme['min_age']: reasons.append("Age too low")
        if u_income > scheme['max_income']: reasons.append("Income too high")
        # ... more checks ...
    return matched, rejected
```

### Hybrid Retrieval (`retrieval.py`)
```python
def hybrid_retrieve(query, eligible_scheme_ids):
    # Keyword Search (BM25)
    bm25_ranked = _bm25_retrieve(query, eligible_set)
    # Semantic Search (ChromaDB)
    chroma_ranked = _chroma_retrieve(query, eligible_set)
    # Fusion
    fused_scores = reciprocal_rank_fusion([bm25_ranked, chroma_ranked])
    return sorted(fused_scores.items())
```

---

## 🚀 Execution Flow Summary
1.  **Input:** User answers profile questions (Name, Caste, Income, etc.).
2.  **Filter:** Rule engine scans `schemes.json` -> Returns "You are eligible for Jagananna Vidya Deevena".
3.  **Chat:** User asks "How do I apply?".
4.  **Retrieve:** System finds text chunks in `schemes.pdf` mentioning "application process" for "Vidya Deevena".
5.  **Response:** LLM summarizes the retrieved text in the user's chosen language (English/Telugu/Hindi).

---
*Created for Claude visibility & contextual understanding.*
