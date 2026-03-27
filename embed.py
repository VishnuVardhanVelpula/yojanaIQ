"""
embed.py — Chunk schemes.pdf by page (one scheme per page),
embed each chunk with sentence-transformers, store in ChromaDB.

Run from inside ap_scheme_rag/ folder:
    python embed.py
"""

import os
import json
import fitz  # PyMuPDF
import chromadb
from sentence_transformers import SentenceTransformer

# ── Paths ─────────────────────────────────────────────────────────────────────
base_dir    = os.path.dirname(os.path.abspath(__file__))
pdf_path    = os.path.join(base_dir, "data", "schemes.pdf")
schemes_path= os.path.join(base_dir, "data", "schemes.json")
chroma_dir  = os.path.join(base_dir, "chroma_db")

# ── Load scheme metadata (for IDs and names as ChromaDB metadata) ─────────────
with open(schemes_path, "r", encoding="utf-8") as f:
    schemes = json.load(f)

# Build a quick id→scheme map
scheme_map = {s["id"]: s for s in schemes}

# ── Extract text per page from PDF ────────────────────────────────────────────
print("📄 Extracting text from PDF...")
doc = fitz.open(pdf_path)

if len(doc) != len(schemes):
    print(f"⚠️  Warning: PDF has {len(doc)} pages but schemes.json has {len(schemes)} schemes.")
    print("   Make sure create_schemes_pdf.py was run after the latest schemes.json.")

chunks = []  # list of dicts: {id, name, category, text}

for page_num, page in enumerate(doc):
    text = page.get_text("text").strip()
    if not text:
        print(f"  ⚠️  Page {page_num+1} has no extractable text — skipping.")
        continue

    # Match page number to scheme (0-indexed)
    if page_num < len(schemes):
        s = schemes[page_num]
        chunks.append({
            "id":       s["id"],
            "name":     s["name"],
            "category": s["category"],
            "text":     text,
        })
        print(f"  ✅ Page {page_num+1}: {s['name']}")
    else:
        print(f"  ⚠️  Page {page_num+1} has no matching scheme — skipping.")

doc.close()
print(f"\n✅ Extracted {len(chunks)} chunks from PDF.\n")

# ── Embed with sentence-transformers ─────────────────────────────────────────
print("🔢 Loading embedding model (all-MiniLM-L6-v2)...")
model = SentenceTransformer("all-MiniLM-L6-v2")

texts = [c["text"] for c in chunks]
print(f"🔢 Embedding {len(texts)} chunks...")
# FIX: newer sentence-transformers removed convert_to_list — use .tolist() instead
embeddings = model.encode(texts, show_progress_bar=True).tolist()
print(f"✅ Embeddings done. Shape: {len(embeddings)} × {len(embeddings[0])}\n")

# ── Store in ChromaDB ─────────────────────────────────────────────────────────
print(f"🗄️  Storing in ChromaDB at: {chroma_dir}")
client = chromadb.PersistentClient(path=chroma_dir)

# Delete existing collection if re-running
try:
    client.delete_collection("ap_schemes")
    print("   (Deleted existing 'ap_schemes' collection — fresh start)")
except Exception:
    pass

collection = client.create_collection(
    name="ap_schemes",
    metadata={"hnsw:space": "cosine"},  # cosine similarity for semantic search
)

collection.add(
    ids        = [c["id"] for c in chunks],
    embeddings = embeddings,
    documents  = [c["text"] for c in chunks],
    metadatas  = [
        {
            "name":     c["name"],
            "category": c["category"],
            "scheme_id": c["id"],
        }
        for c in chunks
    ],
)

print(f"✅ Stored {collection.count()} schemes in ChromaDB collection 'ap_schemes'.\n")

# ── Quick sanity test ─────────────────────────────────────────────────────────
print("🔍 Sanity check — querying: 'scholarship for BC students'")
test_emb = model.encode(["scholarship for BC students"]).tolist()
results  = collection.query(query_embeddings=test_emb, n_results=3)

print("Top 3 matches:")
for i, (doc_text, meta) in enumerate(zip(results["documents"][0], results["metadatas"][0])):
    print(f"  {i+1}. {meta['name']} ({meta['category']})")
    print(f"     Preview: {doc_text[:120].strip()}...")
    print()

print("🎉 embed.py complete! ChromaDB is ready for RAG queries.")