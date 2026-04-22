#!/usr/bin/env python3
"""
embed_search.py
Simple local embedding search with sentence-transformers + faiss.

Usage examples:
  Build index:   python embed_search.py build --source ./texts --index_path index.faiss --meta_path meta.json
  Search:        python embed_search.py search --index_path index.faiss --meta_path meta.json --query "your search here" --k 5
  Add file:      python embed_search.py add --index_path index.faiss --meta_path meta.json --file ./texts/new.txt
"""

from __future__ import annotations
import os
import json
import argparse
from typing import List, Dict, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import faiss

# ---- Config ----
EMBED_MODEL = "all-MiniLM-L6-v2"  # small, fast, good general embeddings
CHUNK_SIZE = 512  # characters per chunk (tweak for your docs)
CHUNK_OVERLAP = 64  # overlap between chunks
D_TYPE = np.float32

# ---- Utilities ----
def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Split text into overlapping chunks (by characters)."""
    if chunk_size <= 0:
        return [text]
    chunks: List[str] = []
    start = 0
    length = len(text)
    while start < length:
        end = min(start + chunk_size, length)
        chunks.append(text[start:end].strip())
        if end == length:
            break
        start = max(0, end - overlap)
    return chunks

def load_text_files_from_folder(folder: str, ext: Tuple[str, ...] = (".txt",)) -> List[Tuple[str, str]]:
    """Return list of (filename, content) for supported extensions."""
    docs: List[Tuple[str, str]] = []
    for root, _, files in os.walk(folder):
        for fn in files:
            if fn.lower().endswith(ext):
                path = os.path.join(root, fn)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        text = f.read()
                except Exception:
                    # fallback to latin1 if utf-8 fails
                    with open(path, "r", encoding="latin1") as f:
                        text = f.read()
                docs.append((path, text))
    return docs

# ---- Embedding + Index management ----
class EmbeddingIndex:
    def __init__(self, model_name: str = EMBED_MODEL):
        self.model = SentenceTransformer(model_name)
        self.index: faiss.Index = None  # will be created after we know dim
        self.id_to_meta: Dict[int, Dict] = {}
        self.next_id = 0

    def _ensure_index(self, dim: int):
        # Use inner product on L2-normalized vectors to get cosine similarity search
        if self.index is None:
            self.index = faiss.IndexFlatIP(dim)
        return self.index

    def embed_texts(self, texts: List[str], batch_size: int = 64) -> np.ndarray:
        """Embed a list of texts -> numpy array (n, dim)."""
        embs = self.model.encode(texts, batch_size=batch_size, show_progress_bar=False, convert_to_numpy=True)
        # normalize to unit length for cosine similarity
        faiss.normalize_L2(embs)
        return embs.astype(D_TYPE)

    def build_from_documents(self, docs: List[Tuple[str, str]]):
        """Docs is list of (source_path, content). This will chunk and index them."""
        all_chunks: List[str] = []
        metas: List[Dict] = []
        for path, content in docs:
            chunks = chunk_text(content)
            for i, c in enumerate(chunks):
                all_chunks.append(c)
                metas.append({"source": path, "chunk_index": i, "text": c[:1000]})  # store snippet
        if not all_chunks:
            raise ValueError("No text chunks found to index.")
        vectors = self.embed_texts(all_chunks)
        dim = vectors.shape[1]
        self._ensure_index(dim)
        self.index.add(vectors)
        # store metadata mapping
        start_id = self.next_id
        for i, m in enumerate(metas):
            self.id_to_meta[start_id + i] = m
        self.next_id += len(metas)
        return len(metas)

    def add_single_file(self, path: str):
        """Read single file, chunk, embed, and add to index."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
        except Exception:
            with open(path, "r", encoding="latin1") as f:
                text = f.read()
        chunks = chunk_text(text)
        if not chunks:
            return 0
        vectors = self.embed_texts(chunks)
        dim = vectors.shape[1]
        self._ensure_index(dim)
        self.index.add(vectors)
        start_id = self.next_id
        for i, c in enumerate(chunks):
            self.id_to_meta[start_id + i] = {"source": path, "chunk_index": i, "text": c[:1000]}
        self.next_id += len(chunks)
        return len(chunks)

    def search(self, query: str, k: int = 5) -> List[Dict]:
        vec = self.embed_texts([query])
        if self.index is None or self.index.ntotal == 0:
            return []
        D, I = self.index.search(vec, k)
        results: List[Dict] = []
        for score, idx in zip(D[0], I[0]):
            if idx < 0:
                continue
            meta = self.id_to_meta.get(int(idx), {})
            results.append({"score": float(score), "id": int(idx), "meta": meta})
        return results

    def save(self, index_path: str, meta_path: str):
        """Save FAISS index and metadata to disk."""
        if self.index is None:
            raise RuntimeError("Index is empty.")
        faiss.write_index(self.index, index_path)
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump({"next_id": self.next_id, "id_to_meta": self.id_to_meta}, f, ensure_ascii=False, indent=2)

    def load(self, index_path: str, meta_path: str):
        """Load FAISS index and metadata from disk."""
        if not os.path.exists(index_path) or not os.path.exists(meta_path):
            raise FileNotFoundError("Index or metadata file not found.")
        self.index = faiss.read_index(index_path)
        with open(meta_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.next_id = data.get("next_id", 0)
        # keys in JSON will be strings — convert to ints
        id_to_meta_raw = data.get("id_to_meta", {})
        self.id_to_meta = {int(k): v for k, v in id_to_meta_raw.items()}

# ---- CLI ----
def main():
    parser = argparse.ArgumentParser(description="Embedding search (local) with sentence-transformers + faiss")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # build
    p_build = sub.add_parser("build", help="Build index from folder of .txt")
    p_build.add_argument("--source", required=True)
    p_build.add_argument("--index_path", required=True)
    p_build.add_argument("--meta_path", required=True)

    # search
    p_search = sub.add_parser("search", help="Search the index")
    p_search.add_argument("--index_path", required=True)
    p_search.add_argument("--meta_path", required=True)
    p_search.add_argument("--query", required=True)
    p_search.add_argument("--k", type=int, default=5)

    # add
    p_add = sub.add_parser("add", help="Add single file to existing index")
    p_add.add_argument("--index_path", required=True)
    p_add.add_argument("--meta_path", required=True)
    p_add.add_argument("--file", required=True)

    args = parser.parse_args()

    ei = EmbeddingIndex()

    if args.cmd == "build":
        docs = load_text_files_from_folder(args.source)
        total = ei.build_from_documents(docs)
        ei.save(args.index_path, args.meta_path)
        print(f"Built index with {total} chunks. Saved to {args.index_path} and {args.meta_path}.")

    elif args.cmd == "search":
        ei.load(args.index_path, args.meta_path)
        results = ei.search(args.query, k=args.k)
        if not results:
            print("No results (index empty or no matches).")
            return
        for r in results:
            meta = r["meta"]
            print(f"score={r['score']:.4f} id={r['id']} source={meta.get('source')} chunk={meta.get('chunk_index')}")
            snippet = meta.get("text", "")
            print(f"  snippet: {snippet[:400].replace('\\n',' ')}")
            print("-" * 60)

    elif args.cmd == "add":
        # load existing index, add file, save back
        ei.load(args.index_path, args.meta_path)
        added = ei.add_single_file(args.file)
        ei.save(args.index_path, args.meta_path)
        print(f"Added {added} chunks from {args.file} and saved index.")

if __name__ == "__main__":
    main()
