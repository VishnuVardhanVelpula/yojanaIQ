import logging
from sentence_transformers import CrossEncoder

logger = logging.getLogger(__name__)

MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"
_reranker = None

def get_reranker():
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoder(MODEL_NAME)
        logger.info(f"CrossEncoder {MODEL_NAME} loaded.")
    return _reranker

def rerank(query: str, chunks: list[dict], top_k: int = 3) -> list[dict]:
    """
    Reranks a list of chunks based on cross-encoder similarity to the query.
    Requires chunks to be a list of dictionaries, each with a 'text' key.
    Adds a 'rerank_score' to each returned chunk.
    """
    if not chunks:
        return []
        
    model = get_reranker()
    
    # CrossEncoder model expects list of pairs: [[query, text1], [query, text2], ...]
    pairs = [[query, c["text"]] for c in chunks]
    
    scores = model.predict(pairs)
    
    # Add scores to chunks
    for i, c in enumerate(chunks):
        c["rerank_score"] = float(scores[i])
        
    # Sort descending by score
    chunks.sort(key=lambda x: x["rerank_score"], reverse=True)
    
    return chunks[:top_k]
