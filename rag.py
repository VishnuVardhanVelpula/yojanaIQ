"""
rag.py — Core RAG pipeline:
  1. Run rule_filter on user profile → hard-matched schemes
  2. Embed a natural language query → retrieve top-k chunks from ChromaDB
  3. Keep only chunks whose scheme_id is in the rule-matched set
  4. Build a prompt and call Groq LLM
  5. Return the LLM response

Run from inside ap_scheme_rag/ folder:
    python rag.py
"""

import os
import json
from dotenv import load_dotenv
from groq import Groq
import chromadb
from sentence_transformers import SentenceTransformer

from rule_filter import rule_filter

# ── Config ────────────────────────────────────────────────────────────────────
load_dotenv()
base_dir   = os.path.dirname(os.path.abspath(__file__))
chroma_dir = os.path.join(base_dir, "chroma_db")

GROQ_MODEL = "llama-3.1-8b-instant"   # fast and free; swap to llama3-70b-8192 for better quality
TOP_K      = 5                   # how many ChromaDB chunks to retrieve before filtering

# ── Load resources once (module-level so app.py can import without re-loading) ─
print("🔧 Loading embedding model...")
_embedder  = SentenceTransformer("all-MiniLM-L6-v2")

print("🗄️  Connecting to ChromaDB...")
_chroma    = chromadb.PersistentClient(path=chroma_dir)
_collection = _chroma.get_collection("ap_schemes")

print("🤖 Connecting to Groq...")
_groq = Groq(api_key=os.environ["GROQ_API_KEY"])

print("✅ All resources loaded.\n")


# ── Main RAG function ─────────────────────────────────────────────────────────
def run_rag(user_profile: dict, user_query: str = "", language: str = "English") -> dict:
    """
    Parameters
    ----------
    user_profile : dict with keys:
        age, gender, caste, religion, occupation, income, flags (list)
    user_query : str
        Optional free-text question from the user. If empty, a default
        query is built from the profile.

    Returns
    -------
    dict with keys:
        answer        : str  — LLM response
        matched_names : list — scheme names that passed rule filter
        retrieved_ids : list — scheme ids actually sent to LLM
    """

    # ── Step 1: Hard rule filter ───────────────────────────────────────────────
    matched, rejected = rule_filter(user_profile)
    matched_ids   = {s["id"] for s in matched}
    matched_names = [s["name"] for s in matched]

    if not matched:
        return {
            "answer": (
                "Based on your profile, no government schemes currently match your eligibility. "
                "Please verify your details or visit your nearest MeeSeva / Ward Secretariat for guidance."
            ),
            "matched_names": [],
            "retrieved_ids": [],
        }

    # ── Step 2: Build semantic query ──────────────────────────────────────────
    if not user_query.strip():
        user_query = (
            f"Government schemes for a {user_profile['age']}-year-old "
            f"{user_profile['gender']} {user_profile['caste']} {user_profile['occupation']} "
            f"with annual income Rs.{user_profile['income']:,} "
            f"in Andhra Pradesh"
        )

    query_emb = _embedder.encode([user_query]).tolist()

    # ── Step 3: Retrieve from ChromaDB and filter to rule-matched only ─────────
    # Retrieve more than TOP_K so we have room to filter
    raw_results = _collection.query(
        query_embeddings=query_emb,
        n_results=min(TOP_K * 2, _collection.count()),
    )

    retrieved_chunks = []
    for doc_text, meta in zip(raw_results["documents"][0], raw_results["metadatas"][0]):
        if meta["scheme_id"] in matched_ids:
            retrieved_chunks.append({
                "id":   meta["scheme_id"],
                "name": meta["name"],
                "text": doc_text,
            })
        if len(retrieved_chunks) >= TOP_K:
            break

    # Fallback: if semantic retrieval missed some matched schemes, append them
    retrieved_ids = {c["id"] for c in retrieved_chunks}
    for s in matched:
        if s["id"] not in retrieved_ids and len(retrieved_chunks) < TOP_K + 3:
            # fetch from ChromaDB by id
            try:
                res = _collection.get(ids=[s["id"]], include=["documents", "metadatas"])
                if res["documents"]:
                    retrieved_chunks.append({
                        "id":   s["id"],
                        "name": s["name"],
                        "text": res["documents"][0],
                    })
            except Exception:
                pass

    # ── Step 4: Build prompt ───────────────────────────────────────────────────
    profile_str = (
        f"Age: {user_profile['age']}, Gender: {user_profile['gender']}, "
        f"Caste: {user_profile['caste']}, Religion: {user_profile['religion']}, "
        f"Occupation: {user_profile['occupation']}, "
        f"Annual Income: Rs.{user_profile['income']:,}, "
        f"Special flags: {user_profile.get('flags', []) or 'None'}"
    )

    context_blocks = "\n\n---\n\n".join(
        f"SCHEME: {c['name']}\n{c['text']}" for c in retrieved_chunks
    )

    system_prompt = f"""You are an elite AP Government welfare scheme advisor.
Your primary job is to explain schemes accurately based ONLY on the scheme context provided below.
IMPORTANT RULES:
1. If the user asks about ONE specific scheme, explain ONLY that requested scheme in full detail.
2. STRICT LANGUAGE OVERRIDE: You MUST write your ENTIRE final response exclusively and strictly in the '{language}' language. Do not output English if {language} is not English!
3. Be clear, warm, and highly professional.
4. If the user asks general questions about documents (e.g., "What is an Income Certificate?" or "How to get an Aadhaar?"), you MAY use your general knowledge to define and explain those documents clearly.
5. Do NOT invent or hallucinate any actual scheme names, benefit amounts, or non-existent rules."""

    user_message = f"""User Profile:
{profile_str}

User Question:
{user_query}

Available Context:
{context_blocks}

Based on the context and profile, directly and exclusively answer the User Question."""

    # ── Step 5: Call Groq LLM ─────────────────────────────────────────────────
    response = _groq.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ],
        temperature=0.4,
        max_tokens=1500,
    )

    answer = response.choices[0].message.content.strip()

    return {
        "answer":        answer,
        "matched_names": matched_names,
        "retrieved_ids": [c["id"] for c in retrieved_chunks],
    }


# ── Quick test ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    test_profile = {
        "age":        22,
        "gender":     "female",
        "caste":      "BC",
        "religion":   "Hindu",
        "occupation": "student",
        "income":     180000,
        "flags":      []
    }

    print("=" * 60)
    print("TEST PROFILE:", test_profile)
    print("=" * 60)

    result = run_rag(test_profile, user_query="What schemes am I eligible for?")

    print(f"\n✅ Rule-matched schemes ({len(result['matched_names'])}):")
    for name in result["matched_names"]:
        print(f"   • {name}")

    print(f"\n📚 Schemes sent to LLM ({len(result['retrieved_ids'])}):")
    for sid in result["retrieved_ids"]:
        print(f"   • {sid}")

    print("\n🤖 LLM Response:")
    print("-" * 60)
    print(result["answer"])
    print("-" * 60)