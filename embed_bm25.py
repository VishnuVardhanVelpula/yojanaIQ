# embed_bm25.py
# Run once: python embed_bm25.py
# Builds BM25 corpus from schemes.pdf and saves to data/bm25_corpus.pkl

import fitz
import pickle
import re
import os
import json
from pathlib import Path

base_dir = os.path.dirname(os.path.abspath(__file__))

def tokenize(text: str) -> list[str]:
    """Lowercase, strip punctuation, split on whitespace."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return text.split()

def build_bm25_corpus(pdf_path: str = os.path.join(base_dir, "data", "schemes.pdf"),
                      json_path: str = os.path.join(base_dir, "data", "schemes.json"),
                      out_path: str = os.path.join(base_dir, "data", "bm25_corpus.pkl")):
    
    print("Loading schemes.json for precise IDs...")
    with open(json_path, "r", encoding="utf-8") as f:
        schemes = json.load(f)

    print("Extracting text from PDF...")
    doc = fitz.open(pdf_path)
    
    corpus_tokens = []
    corpus_texts  = []
    chunk_ids     = []

    for page_num, page in enumerate(doc):
        text = page.get_text("text").strip()
        if not text:
            continue
            
        # Match page to scheme just like ChromaDB embed.py
        if page_num < len(schemes):
            s = schemes[page_num]
            chunk_ids.append(s["id"])
            
            tokens = tokenize(text)
            corpus_tokens.append(tokens)
            corpus_texts.append(text)
        else:
            print(f"  ⚠️  Page {page_num+1} has no matching scheme in json — skipping.")

    payload = {
        "corpus_tokens": corpus_tokens,
        "corpus_texts":  corpus_texts,
        "chunk_ids":     chunk_ids,
        "chunk_names":   [s["name"] for s in schemes[:len(chunk_ids)]]
    }
    
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as f:
        pickle.dump(payload, f)

    print(f"BM25 corpus built: {len(corpus_tokens)} chunks -> {out_path}")

if __name__ == "__main__":
    build_bm25_corpus()
