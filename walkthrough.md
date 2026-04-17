# Hybrid RRF Retrieval Pipeline Walkthrough

I have successfully integrated the `hybrid_retrieve` pipeline replacing the legacy semantic search, preserving its metadata matching architecture.

## Changes Made
- Added `rank-bm25` module to your virtual environment and `requirements.txt`.
- Created **`embed_bm25.py`** and modified it from the original Claude plan so that the BM25 chunks correspond precisely to the `scheme_id` strings (like `annadata_sukhibhava`) from your `schemes.json` file.
- Built **`retrieval.py`** to natively implement Reciprocal Rank Fusion (RRF), comparing BM25 rank scores directly to ChromaDB rank scores using the shared UUID schema, preventing any fallback onto fuzzy matching.
- Hooked `hybrid_retrieve` into **`rag.py`**, upgrading Step 4 of the main RAG function to accept and render retrieved sources tagging (e.g. `'bm25'`, `'chroma'`, or `'bm25+chroma'`).

## What Was Tested
- The script successfully serialized the exact same corpus texts/IDs from `data/schemes.json` utilizing `fitz` into the BM25 space inside `data/bm25_corpus.pkl`.
- Tested RRF outputs directly routing down to the `rag.py` tests. The query-type detector, missing contexts guard rails, and rule filters seamlessly inherited the newly processed multi-source `retrieved_chunks`.

> [!TIP]
> **To proceed with your IEEE Report Ablations:**
> The field `retrieval_sources` inside the `run_rag()` output dictionary now indicates exactly what source (`bm25`, `chroma`, `bm25+chroma`) the model relied on for generating its prompt context blocks. You can directly log this array inside your final `csv` logs while grading on RAGAS frameworks to prove overlapping verification.
