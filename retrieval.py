# retrieval.py
# Hybrid BM25 + ChromaDB retrieval with Reciprocal Rank Fusion (RRF)

import pickle
import logging
import os
from typing import Optional
from rank_bm25 import BM25Okapi
import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

base_dir = os.path.dirname(os.path.abspath(__file__))

# ── Constants ────────────────────────────────────────────────────────────────
BM25_CORPUS_PATH  = os.path.join(base_dir, "data", "bm25_corpus.pkl")
CHROMA_DB_PATH    = os.path.join(base_dir, "chroma_db")
CHROMA_COLLECTION = "ap_schemes"
EMBED_MODEL       = "all-MiniLM-L6-v2"

BM25_TOP_K        = 10   # candidates from BM25 before fusion
CHROMA_TOP_K      = 10   # candidates from ChromaDB before fusion
RRF_K             = 60   # RRF damping constant (cite: Cormack et al. 2009)
FINAL_TOP_K       = 5    # chunks returned to the LLM after fusion

# ── Lazy singletons (load once per process) ──────────────────────────────────
_bm25_index:    Optional[BM25Okapi]       = None
_bm25_payload:  Optional[dict]            = None
_chroma_col:    Optional[object]          = None
_embedder:      Optional[SentenceTransformer] = None


def _load_bm25():
    global _bm25_index, _bm25_payload
    if _bm25_index is None:
        with open(BM25_CORPUS_PATH, "rb") as f:
            _bm25_payload = pickle.load(f)
        _bm25_index = BM25Okapi(_bm25_payload["corpus_tokens"])
        logger.info("BM25 index loaded (%d chunks)", len(_bm25_payload["corpus_tokens"]))
    return _bm25_index, _bm25_payload


def _load_chroma():
    global _chroma_col
    if _chroma_col is None:
        client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        _chroma_col = client.get_collection(
            name=CHROMA_COLLECTION
        )
        logger.info("ChromaDB collection loaded")
    return _chroma_col

def _load_embedder():
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer(EMBED_MODEL)
        logger.info("Embedder loaded: %s", EMBED_MODEL)
    return _embedder

# ── Core RRF function ─────────────────────────────────────────────────────────
def reciprocal_rank_fusion(
    ranked_lists: list[list[str]],
    k: int = RRF_K
) -> dict[str, float]:
    """
    Fuse N ranked lists of chunk IDs using RRF.
    Returns {chunk_id: rrf_score} — higher is better.
    """
    scores: dict[str, float] = {}
    for ranked in ranked_lists:
        for rank, chunk_id in enumerate(ranked):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank + 1)
    return scores

# ── BM25 retrieval ────────────────────────────────────────────────────────────
def _bm25_retrieve(query: str, eligible_ids: set[str], top_k: int) -> list[str]:
    """Return top_k chunk IDs from BM25, filtered to eligible_ids."""
    bm25, payload = _load_bm25()
    tokens  = query.lower().split()
    scores  = bm25.get_scores(tokens)

    ranked = sorted(
        range(len(scores)),
        key=lambda i: scores[i],
        reverse=True
    )

    results = []
    for idx in ranked:
        cid = payload["chunk_ids"][idx]
        if cid in eligible_ids:
            results.append(cid)
        if len(results) >= top_k:
            break
    return results

# ── ChromaDB retrieval ────────────────────────────────────────────────────────
def _chroma_retrieve(query: str, eligible_ids: set[str], top_k: int) -> list[str]:
    """Return top_k chunk IDs from ChromaDB semantic search, filtered to eligible_ids."""
    col = _load_chroma()
    embedder = _load_embedder()
    query_vec = embedder.encode([query]).tolist()[0]

    results = col.query(
        query_embeddings=[query_vec],
        n_results=top_k,
        where={"scheme_id": {"$in": list(eligible_ids)}},
        include=["documents", "metadatas", "distances"]
    )
    return results["ids"][0] if results["ids"] else []

# ── Hybrid retrieve: the main public API ─────────────────────────────────────
def hybrid_retrieve(
    query: str,
    eligible_scheme_ids: list[str],
    top_k: int = FINAL_TOP_K,
    rrf_k: int = RRF_K,
    bm25_k: int = BM25_TOP_K,
    chroma_k: int = CHROMA_TOP_K,
    return_texts: bool = True,
) -> list[dict]:
    """
    Hybrid BM25 + ChromaDB retrieval fused with RRF.

    Args:
        query:               Natural language user query.
        eligible_scheme_ids: Scheme IDs from rule_filter.
        top_k:               Number of chunks to return after fusion.
        rrf_k:               RRF damping constant.
        bm25_k:              BM25 candidate pool size before fusion.
        chroma_k:            ChromaDB candidate pool size before fusion.
        return_texts:        If True, include chunk text & name in results.

    Returns:
        List of dicts: [{chunk_id, rrf_score, source, text, name}, ...]
        Sorted descending by rrf_score.
    """
    _, payload = _load_bm25()

    eligible_set = set(eligible_scheme_ids)

    if not eligible_set:
        logger.warning("No eligible chunks found for schemes: %s", eligible_scheme_ids)
        return []

    # Retrieve candidates from both retrievers
    bm25_ranked   = _bm25_retrieve(query, eligible_set, bm25_k)
    chroma_ranked = _chroma_retrieve(query, eligible_set, chroma_k)

    logger.debug("BM25 top-%d: %s", bm25_k, bm25_ranked[:3])
    logger.debug("Chroma top-%d: %s", chroma_k, chroma_ranked[:3])

    # Fuse with RRF
    fused_scores = reciprocal_rank_fusion(
        [bm25_ranked, chroma_ranked],
        k=rrf_k
    )

    # Sort and take top_k
    ranked_final = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

    # Build result dicts
    chunk_id_to_idx = {cid: i for i, cid in enumerate(payload["chunk_ids"])}
    results = []
    for chunk_id, score in ranked_final:
        idx = chunk_id_to_idx.get(chunk_id)
        entry = {
            "chunk_id":  chunk_id,
            "rrf_score": round(score, 6),
            "source":    "bm25+chroma" if (chunk_id in bm25_ranked and chunk_id in chroma_ranked)
                         else ("bm25" if chunk_id in bm25_ranked else "chroma"),
        }
        if return_texts and idx is not None:
            entry["text"] = payload["corpus_texts"][idx]
            entry["name"] = payload["chunk_names"][idx]
        results.append(entry)

    logger.info(
        "Hybrid retrieve: query=%r  eligible_chunks=%d  fused=%d  returned=%d",
        query[:60], len(eligible_set), len(fused_scores), len(results)
    )
    return results
