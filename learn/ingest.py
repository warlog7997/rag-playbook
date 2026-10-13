"""
Ingest NovaDash knowledge base into ChromaDB and build BM25 index.
Run this once before any learn module examples.

Usage: python ingest.py
"""
import os
import pickle
import sys
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi

KB_DIR = Path(__file__).parent.parent / "knowledge-base"
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

CHROMA_PATH = str(DATA_DIR / "chromadb")
BM25_PATH = DATA_DIR / "bm25_index.pkl"
COLLECTION_NAME = "novadash_docs"


def load_and_chunk_docs():
    """Load markdown files and split into sections by ## headers."""
    chunks = []
    for md_file in sorted(KB_DIR.glob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        sections = content.split("\n## ")

        # First section is the file intro (before first ##)
        intro = sections[0].strip()
        if intro:
            chunks.append({
                "id": f"{md_file.stem}::intro",
                "text": intro,
                "source": md_file.name,
                "section": "intro",
            })

        # Remaining sections
        for section in sections[1:]:
            lines = section.strip().split("\n")
            section_title = lines[0].strip()
            section_body = "\n".join(lines[1:]).strip()
            if section_body:
                chunks.append({
                    "id": f"{md_file.stem}::{section_title.lower().replace(' ', '_')}",
                    "text": f"## {section_title}\n{section_body}",
                    "source": md_file.name,
                    "section": section_title,
                })

    return chunks


def build_chroma_index(chunks):
    """Embed chunks and store in ChromaDB."""
    print("Loading embedding model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    client = chromadb.PersistentClient(path=CHROMA_PATH)

    # Delete existing collection if rebuilding
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"Deleted existing collection '{COLLECTION_NAME}'")
    except Exception:
        pass

    collection = client.create_collection(COLLECTION_NAME)

    texts = [c["text"] for c in chunks]
    print(f"Embedding {len(chunks)} chunks...")
    embeddings = model.encode(texts, show_progress_bar=True).tolist()

    collection.add(
        ids=[c["id"] for c in chunks],
        documents=texts,
        embeddings=embeddings,
        metadatas=[{"source": c["source"], "section": c["section"]} for c in chunks],
    )

    print(f"ChromaDB: {len(chunks)} chunks stored in '{COLLECTION_NAME}'")
    return collection


def build_bm25_index(chunks):
    """Build BM25 keyword index over all chunks."""
    tokenized = [c["text"].lower().split() for c in chunks]
    bm25 = BM25Okapi(tokenized)
    with open(BM25_PATH, "wb") as f:
        pickle.dump({"bm25": bm25, "chunks": chunks}, f)
    print(f"BM25: index saved to {BM25_PATH}")


if __name__ == "__main__":
    print("=== Ingesting NovaDash Knowledge Base ===\n")

    chunks = load_and_chunk_docs()
    print(f"Loaded {len(chunks)} chunks from {KB_DIR}\n")

    if len(chunks) == 0:
        print("ERROR: No chunks found. Make sure the knowledge-base/ directory has .md files.")
        sys.exit(1)

    build_chroma_index(chunks)
    build_bm25_index(chunks)

    print(f"\nDone! Run any script in learn/ now.")
    print(f"  Example: cd 01-what-is-rag && python demo.py")
