"""
rag.py — YojanaIQ Core RAG Pipeline (Fix #5 — Prompt Engineering Upgrade)
==========================================================================

Changes from original:
  - Rewrote system prompt with hard grounding rules (anti-hallucination)
  - Added structured answer format enforcement
  - Profile-aware answering: LLM cross-references user eligibility while answering
  - Reduced temperature 0.4 → 0.1 for factual grounding
  - Added CONTEXT_MISSING guard: safe fallback if no chunks retrieved
  - Added faithfulness_check(): cosine similarity between answer and context
  - Added detect_query_type(): routes eligibility/how_to_apply/documents/status
  - All other logic (ChromaDB, rule_filter, Groq setup) unchanged from original

Pipeline:
  user_profile + query
        │
        ▼
  rule_filter()           → matched_schemes[], rejected_schemes[]
        │
        ▼
  detect_query_type()     → "eligibility" | "how_to_apply" | "documents" | "status" | "general"
        │
        ▼
  query embedding         → all-MiniLM-L6-v2
        │
        ▼
  ChromaDB retrieval      → top-12 pool, filtered to matched scheme IDs only → top-5
        │
        ▼
  CONTEXT_MISSING guard   → if 0 chunks, return safe fallback immediately
        │
        ▼
  build_prompt()          → system_prompt + profile_block + context_block + query
        │
        ▼
  Groq LLM                → temperature=0.1, max_tokens=1500
        │
        ▼
  faithfulness_check()    → cosine(answer_emb, context_emb) — flags low-confidence
        │
        ▼
  final dict { answer, matched_names, retrieved_ids, confidence, query_type }
"""

import os
import numpy as np
from dotenv import load_dotenv
from groq import Groq
import chromadb
from sentence_transformers import SentenceTransformer

from rule_filter import rule_filter

# ── Config ────────────────────────────────────────────────────────────────────
load_dotenv()
base_dir    = os.path.dirname(os.path.abspath(__file__))
chroma_dir  = os.path.join(base_dir, "chroma_db")

GROQ_MODEL             = "llama-3.1-8b-instant"
TOP_K                  = 5    # max chunks sent to LLM after filtering
RETRIEVAL_POOL         = 12   # raw chunks pulled from ChromaDB before filtering
FAITHFULNESS_THRESHOLD = 0.30 # cosine similarity below this → flag low confidence

# ── Load resources once at module level ───────────────────────────────────────
print("Loading embedding model...")
_embedder   = SentenceTransformer("all-MiniLM-L6-v2")

print("Connecting to ChromaDB...")
_chroma     = chromadb.PersistentClient(path=chroma_dir)
_collection = _chroma.get_collection("ap_schemes")

print("Connecting to Groq...")
_groq = Groq(api_key=os.environ["GROQ_API_KEY"])

print("All resources loaded.\n")


# ── Query type detector ───────────────────────────────────────────────────────
def detect_query_type(query: str) -> str:
    """
    Classify the user query so the prompt gives targeted instructions.
    Returns: "eligibility" | "how_to_apply" | "documents" | "status" | "general"
    """
    q = query.lower()

    apply_kw = [
        "apply", "register", "enroll", "sign up", "how to get",
        "application", "form", "portal", "website", "online",
        "దరఖాస్తు", "అప్లై", "आवेदन",
    ]
    doc_kw = [
        "document", "certificate", "proof", "aadhaar", "ration card",
        "income certificate", "caste certificate", "passbook",
        "పత్రాలు", "సర్టిఫికెట్", "दस्तावेज़",
    ]
    status_kw = [
        "status", "payment", "disbursed", "credited", "check",
        "track", "when", "date", "installment",
        "స్థితి", "చెల్లింపు", "स्थिति", "भुगतान",
    ]
    eligibility_kw = [
        "eligible", "qualify", "who can", "criteria", "am i",
        "can i get", "అర్హత", "पात्रता",
    ]

    if any(k in q for k in apply_kw):
        return "how_to_apply"
    if any(k in q for k in doc_kw):
        return "documents"
    if any(k in q for k in status_kw):
        return "status"
    if any(k in q for k in eligibility_kw):
        return "eligibility"
    return "general"


# ── Faithfulness check ────────────────────────────────────────────────────────
def faithfulness_check(answer: str, context_chunks: list) -> float:
    """
    Cosine similarity between the LLM answer embedding and the
    average context embedding. Score below FAITHFULNESS_THRESHOLD
    suggests the answer diverged from the retrieved context.
    Returns float 0.0–1.0.
    """
    if not context_chunks or not answer.strip():
        return 0.0

    context_text = " ".join(c["text"] for c in context_chunks)
    answer_emb   = _embedder.encode([answer])[0]
    context_emb  = _embedder.encode([context_text])[0]

    dot  = float(np.dot(answer_emb, context_emb))
    norm = float(np.linalg.norm(answer_emb) * np.linalg.norm(context_emb))
    return dot / norm if norm > 0 else 0.0


# ── Safe fallback response ────────────────────────────────────────────────────
_SAFE_FALLBACK = {
    "English": (
        "I don't have enough verified details to answer that accurately. "
        "Please visit your nearest Grama/Ward Sachivalayam or call 1902 for assistance.\n\n"
        "📞 For help: visit your nearest Grama/Ward Sachivalayam or call 1902."
    ),
    "Telugu": (
        "మీ ప్రశ్నకు సరైన సమాచారం నా దగ్గర లేదు. దయచేసి మీ దగ్గరలోని "
        "గ్రామ/వార్డు సచివాలయాన్ని సందర్శించండి లేదా 1902కి కాల్ చేయండి.\n\n"
        "📞 సహాయం: 1902."
    ),
    "Hindi": (
        "मुझे आपके प्रश्न का सटीक उत्तर नहीं मिला। कृपया अपने नजदीकी "
        "ग्राम/वार्ड सचिवालय जाएं या 1902 पर कॉल करें।\n\n"
        "📞 सहायता: 1902."
    ),
}

_LOW_CONFIDENCE_WARNING = {
    "English": (
        "\n\n⚠️ Note: I may not have complete details for this query. "
        "Please verify at your nearest Grama/Ward Sachivalayam or call 1902."
    ),
    "Telugu": (
        "\n\n⚠️ గమనిక: ఈ సమాచారం పూర్తిగా నిర్ధారించబడలేదు. "
        "దయచేసి సచివాలయాన్ని సందర్శించండి లేదా 1902కి కాల్ చేయండి."
    ),
    "Hindi": (
        "\n\n⚠️ नोट: यह जानकारी पूरी तरह सत्यापित नहीं है। "
        "कृपया सचिवालय जाएं या 1902 पर कॉल करें।"
    ),
}


# ── Prompt builder ────────────────────────────────────────────────────────────
def build_prompt(
    user_profile:    dict,
    user_query:      str,
    context_chunks:  list,
    matched_schemes: list,
    query_type:      str,
    language:        str,
) -> tuple:
    """
    Returns (system_prompt: str, user_message: str)
    """

    # Profile block ─────────────────────────────────────────────────────────
    residence = user_profile.get("residence_type", "rural")
    marital   = user_profile.get("marital_status", "married")
    houseless = "Yes" if user_profile.get("houseless", False) else "No"
    flags     = user_profile.get("flags", []) or []

    profile_block = f"""USER PROFILE (verified by eligibility engine — treat as ground truth):
  Age              : {user_profile['age']} years
  Gender           : {user_profile['gender'].title()}
  Caste            : {user_profile['caste']}
  Religion         : {user_profile['religion']}
  Occupation       : {user_profile['occupation']}
  Marital status   : {marital.title()}
  Residence type   : {residence.title()}
  Houseless        : {houseless}
  Annual income    : ₹{user_profile['income']:,}
  Special flags    : {', '.join(flags) if flags else 'None'}"""

    # Confirmed eligible schemes block ──────────────────────────────────────
    schemes_block = (
        "CONFIRMED ELIGIBLE SCHEMES (determined by rule engine — authoritative):\n"
        + "\n".join(f"  • {s['name']}" for s in matched_schemes)
    )

    # Context block ─────────────────────────────────────────────────────────
    context_block = "\n\n---\n\n".join(
        f"[SCHEME: {c['name']} | Score: {c.get('rrf_score', 0)} | Via: {c.get('source', 'rule_injection')}]\n{c['text']}"
        for c in context_chunks
    )

    # Query-type-specific instructions ──────────────────────────────────────
    query_instructions = {

        "how_to_apply": """\
The user wants to know HOW TO APPLY. Structure your answer as follows:
  1. Start with the scheme name as a heading.
  2. List the exact official portal URL (copy from context, do not invent).
  3. Give numbered step-by-step application instructions.
  4. State the offline alternative: Grama/Ward Sachivalayam or Meeseva centre.
  5. Include the helpline number if present in context.
  Do NOT repeat eligibility criteria — the user already qualifies.""",

        "documents": """\
The user wants to know WHAT DOCUMENTS ARE NEEDED. Structure your answer as:
  1. Scheme name as a heading.
  2. Numbered list of every required document from the context.
  3. For each document, one-line note on where to obtain it if not obvious.
  4. Call out EXPLICITLY if Aadhaar must be linked to bank account (NPCI-mapping).
  Do NOT describe application steps unless they clarify a document requirement.""",

        "status": """\
The user wants to CHECK STATUS or PAYMENT. Structure your answer as:
  1. Scheme name as a heading.
  2. Exact status-check portal URL (copy from context only).
  3. Step-by-step: how to check status (Aadhaar / application number / OTP).
  4. Helpline number.
  5. Expected processing time or payment schedule if in context.
  If context lacks status-check info, say so clearly — do not invent a URL.""",

        "eligibility": """\
The user wants to know IF THEY QUALIFY. Structure your answer as:
  1. Scheme name as a heading.
  2. List all eligibility conditions from the context.
  3. For EACH condition, explicitly state whether this user meets it (use their profile).
  4. Conclude with a clear verdict: "You ARE eligible because..." or "You do NOT qualify because..."
  Be precise: reference the user's actual age, income, caste, occupation directly.""",

        "general": """\
Give a comprehensive answer with these clearly headed sections:
  1. What this scheme provides (exact benefit amount from context).
  2. Key eligibility conditions relevant to this user's profile.
  3. How to apply (portal URL + offline option).
  4. Required documents (brief list).
  5. Status check portal and helpline number.
  Be concise — each section should be 2–4 lines maximum.""",
    }

    query_instruction = query_instructions.get(query_type, query_instructions["general"])

    # System prompt ─────────────────────────────────────────────────────────
    system_prompt = f"""You are YojanaIQ — an expert Andhra Pradesh government welfare scheme advisor trusted by citizens across AP.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ABSOLUTE GROUNDING RULES — NEVER VIOLATE THESE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RULE 1 — CONTEXT ONLY:
  Use ONLY the information in the SCHEME CONTEXT below.
  Never use your training knowledge for scheme-specific facts (amounts, portals, documents).
  If the context does not contain the answer → say exactly:
  "I don't have that specific detail. Please visit your nearest Grama/Ward Sachivalayam or call 1902."

RULE 2 — NEVER CONTRADICT THE RULE ENGINE:
  The CONFIRMED ELIGIBLE SCHEMES list is authoritative — it is from a deterministic rule engine.
  Do NOT tell the user they are ineligible for any scheme on that list.
  Do NOT suggest schemes that are NOT on that list.

RULE 3 — NUMBERS ARE SACRED:
  Copy benefit amounts, scheme names, and URLs exactly from context.
  WRONG: "around ₹4,000" or "about Rs 4000/month"
  RIGHT: "₹4,000 per month"
  Never round, paraphrase, or approximate any figure.

RULE 4 — PORTAL URLs MUST BE EXACT:
  Copy URLs character-for-character from context.
  If no URL is in context → do not invent one.

RULE 5 — LANGUAGE LOCK:
  Your ENTIRE response must be written in {language} only.
  Telugu → full Telugu script. Hindi → full Devanagari. English → English.
  Do NOT mix languages unless the user's question explicitly mixed them.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RESPONSE FORMAT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  - Use the scheme name as a bold heading for each scheme discussed.
  - Numbered lists for steps. Bullet points for documents and features.
  - Keep total response under 600 words.
  - End EVERY response with this exact footer line:
    "📞 For help: visit your nearest Grama/Ward Sachivalayam or call 1902."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ANSWER TYPE — FOLLOW THESE SPECIFIC INSTRUCTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{query_instruction}"""

    # User message ───────────────────────────────────────────────────────────
    user_message = f"""{profile_block}

{schemes_block}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SCHEME CONTEXT — YOUR ONLY SOURCE OF TRUTH
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{context_block}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
USER QUESTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{user_query}

Answer using ONLY the scheme context above. Follow all 5 grounding rules.
Do not use any knowledge outside this context window."""

    return system_prompt, user_message


# ── Main RAG function ─────────────────────────────────────────────────────────
def run_rag(
    user_profile: dict,
    user_query:   str = "",
    language:     str = "English",
) -> dict:
    """
    Parameters
    ----------
    user_profile : dict
        Required keys: age, gender, caste, religion, occupation, income
        Optional keys: residence_type, marital_status, houseless, flags

    user_query : str
        Free-text question. If empty, a default eligibility query is built.

    language : str
        "English" | "Telugu" | "Hindi"

    Returns
    -------
    dict:
        answer         : str   — LLM answer (grounded)
        matched_names  : list  — scheme names from rule engine
        retrieved_ids  : list  — scheme IDs sent to LLM
        confidence     : float — faithfulness score 0.0–1.0
        query_type     : str   — detected intent
        low_confidence : bool  — True if answer may not be grounded
    """

    # Step 1 — Hard rule filter ────────────────────────────────────────────────
    matched, _ = rule_filter(user_profile)
    matched_ids   = {s["id"] for s in matched}
    matched_names = [s["name"] for s in matched]

    if not matched:
        return {
            "answer": (
                "Based on your profile, no government schemes currently match your "
                "eligibility criteria. Please verify your details or visit your nearest "
                "MeeSeva centre or Grama/Ward Sachivalayam for guidance.\n\n"
                "📞 For help: visit your nearest Grama/Ward Sachivalayam or call 1902."
            ),
            "matched_names": [],
            "retrieved_ids": [],
            "retrieved_chunks": [],
            "retrieval_sources": [],
            "confidence":    1.0,
            "query_type":    "eligibility",
            "low_confidence": False,
        }

    # Step 2 — Detect query intent ─────────────────────────────────────────────
    query_type = detect_query_type(user_query)

    # Step 3 — Default query if empty ──────────────────────────────────────────
    if not user_query.strip():
        residence  = user_profile.get("residence_type", "rural")
        marital    = user_profile.get("marital_status", "married")
        user_query = (
            f"What government schemes am I eligible for? "
            f"I am a {user_profile['age']}-year-old {marital} "
            f"{user_profile['gender']} {user_profile['caste']} "
            f"{user_profile['occupation']} living in a {residence} area "
            f"with annual income ₹{user_profile['income']:,} in Andhra Pradesh."
        )
        query_type = "eligibility"

    # Step 4 — Embed and retrieve (Hybrid) ─────────────────────────────────────
    from retrieval import hybrid_retrieve
    from reranker import rerank
    
    chunks = hybrid_retrieve(
        query=user_query,
        eligible_scheme_ids=list(matched_ids),
        top_k=TOP_K,
        rrf_k=60,
    )
    
    chunks = rerank(query=user_query, chunks=chunks, top_k=3)

    retrieved_chunks = []
    for c in chunks:
        retrieved_chunks.append({
            "id": c["chunk_id"],
            "name": c.get("name", c["chunk_id"]),
            "text": c["text"],
            "source": c["source"],
            "rrf_score": c.get("rrf_score", 0.0),
            "rerank_score": c.get("rerank_score", 0.0)
        })

    # Inject any rule-matched scheme missing from semantic results
    retrieved_ids_set = {c["id"] for c in retrieved_chunks}
    for s in matched:
        if s["id"] not in retrieved_ids_set and len(retrieved_chunks) < TOP_K:
            try:
                res = _collection.get(ids=[s["id"]], include=["documents", "metadatas"])
                if res["documents"]:
                    retrieved_chunks.append({
                        "id":   s["id"],
                        "name": s["name"],
                        "text": res["documents"][0],
                        "source": "rule_injection",
                        "rrf_score": 0.0,
                        "rerank_score": 0.0
                    })
            except Exception:
                pass

    # Step 5 — CONTEXT_MISSING guard ───────────────────────────────────────────
    if not retrieved_chunks:
        return {
            "answer":        _SAFE_FALLBACK.get(language, _SAFE_FALLBACK["English"]),
            "matched_names": matched_names,
            "retrieved_ids": [],
            "retrieved_chunks": [],
            "retrieval_sources": [],
            "confidence":    0.0,
            "query_type":    query_type,
            "low_confidence": True,
        }

    # Step 6 — Build prompt ────────────────────────────────────────────────────
    system_prompt, user_message = build_prompt(
        user_profile    = user_profile,
        user_query      = user_query,
        context_chunks  = retrieved_chunks,
        matched_schemes = matched,
        query_type      = query_type,
        language        = language,
    )

    # Step 7 — Call Groq LLM ───────────────────────────────────────────────────
    response = _groq.chat.completions.create(
        model    = GROQ_MODEL,
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ],
        temperature = 0.1,   # Low for factual accuracy
        max_tokens  = 1500,
    )

    answer = response.choices[0].message.content.strip()

    # Step 8 — Faithfulness check ──────────────────────────────────────────────
    confidence     = faithfulness_check(answer, retrieved_chunks)
    low_confidence = confidence < FAITHFULNESS_THRESHOLD

    if low_confidence:
        answer += _LOW_CONFIDENCE_WARNING.get(language, _LOW_CONFIDENCE_WARNING["English"])

    return {
        "answer":        answer,
        "matched_names": matched_names,
        "retrieved_ids": [c["id"] for c in retrieved_chunks],
        "retrieved_chunks": retrieved_chunks,
        "retrieval_sources": [c.get("source", "rule_injection") for c in retrieved_chunks],
        "confidence":    round(confidence, 3),
        "query_type":    query_type,
        "low_confidence": low_confidence,
    }


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    test_cases = [
        {
            "label":   "BC student — how to apply for scholarship",
            "profile": {
                "age": 20, "gender": "female", "caste": "BC",
                "religion": "Hindu", "occupation": "student",
                "income": 180000, "residence_type": "rural",
                "marital_status": "single", "houseless": False, "flags": [],
            },
            "query": "How do I apply for Post Matric Scholarship? What portal do I use?",
        },
        {
            "label":   "Farmer — Annadata Sukhibhava documents",
            "profile": {
                "age": 45, "gender": "male", "caste": "OC",
                "religion": "Hindu", "occupation": "farmer",
                "income": 120000, "residence_type": "rural",
                "marital_status": "married", "houseless": False, "flags": [],
            },
            "query": "What documents do I need for Annadata Sukhibhava?",
        },
        {
            "label":   "Senior citizen — NTR Bharosa pension status",
            "profile": {
                "age": 68, "gender": "male", "caste": "SC",
                "religion": "Hindu", "occupation": "none",
                "income": 60000, "residence_type": "rural",
                "marital_status": "married", "houseless": False, "flags": [],
            },
            "query": "How can I check my NTR Bharosa pension payment status?",
        },
        {
            "label":   "Widow — Telugu language test",
            "profile": {
                "age": 52, "gender": "female", "caste": "BC",
                "religion": "Hindu", "occupation": "none",
                "income": 80000, "residence_type": "rural",
                "marital_status": "widowed", "houseless": False, "flags": [],
            },
            "query": "నాకు ఏ పెన్షన్ వస్తుంది? ఎంత వస్తుంది?",
            "lang":  "Telugu",
        },
    ]

    for case in test_cases:
        lang = case.get("lang", "English")
        print("\n" + "=" * 70)
        print(f"TEST  : {case['label']}")
        print(f"LANG  : {lang}")
        print(f"QUERY : {case['query']}")
        print("=" * 70)

        result = run_rag(
            user_profile = case["profile"],
            user_query   = case["query"],
            language     = lang,
        )

        conf_flag = "LOW - may be hallucinated" if result["low_confidence"] else "OK"
        print(f"Query type   : {result['query_type']}")
        print(f"Confidence   : {result['confidence']}  {conf_flag}")
        print(f"Matched      : {len(result['matched_names'])} schemes")
        print(f"Retrieved    : {result['retrieved_ids']}")
        print(f"Sources      : {result['retrieval_sources']}")
        print("\nAnswer:")
        print("-" * 70)
        print(result["answer"])
        print("-" * 70)


def answer_query(user_profile: dict, query: str = "", language: str = "English") -> dict:
    """Wrapper to map legacy call formats to run_rag for Evaluation framework."""
    return run_rag(user_profile, query, language)