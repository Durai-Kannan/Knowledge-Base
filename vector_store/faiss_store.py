import os
import json
import faiss
import numpy as np
from pathlib import Path
from .embeddings import generate_embeddings

try:
    from django.conf import settings
    if settings.configured:
        VECTOR_DATA_DIR = Path(getattr(settings, 'VECTOR_DATA_DIR', Path(__file__).resolve().parent.parent / 'vector_data'))
    else:
        VECTOR_DATA_DIR = Path(__file__).resolve().parent.parent / 'vector_data'
except Exception:
    VECTOR_DATA_DIR = Path(__file__).resolve().parent.parent / 'vector_data'
INDEX_FILE = VECTOR_DATA_DIR / 'index.faiss'
METADATA_FILE = VECTOR_DATA_DIR / 'metadata.json'
VECTOR_DIMENSION = 384


class FAISSVectorStore:
    def __init__(self):
        VECTOR_DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.index = None
        self.metadata = {}
        self.load()

    def load(self):
        """Loads FAISS index and metadata from disk if available."""
        if INDEX_FILE.exists() and METADATA_FILE.exists():
            try:
                self.index = faiss.read_index(str(INDEX_FILE))
                with open(METADATA_FILE, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
            except Exception as e:
                print(f"[FAISSStore] Warning loading index: {e}, initializing fresh index.")
                self._init_fresh_index()
        else:
            self._init_fresh_index()

    def _init_fresh_index(self):
        # IndexFlatIP uses Inner Product (Cosine similarity when vectors are L2 normalized)
        self.index = faiss.IndexFlatIP(VECTOR_DIMENSION)
        self.metadata = {}

    def save(self):
        """Saves FAISS index and metadata mapping to disk."""
        VECTOR_DATA_DIR.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(INDEX_FILE))
        with open(METADATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)

    def add_chunks(self, chunk_data_list: list[dict]):
        """
        Adds a batch of chunks to FAISS index and metadata store.
        Each item in chunk_data_list should be a dict:
        {
            'chunk_id': int,
            'document_id': int,
            'url': str,
            'title': str,
            'chunk_index': int,
            'content': str
        }
        Returns list of embedding IDs assigned in FAISS.
        """
        if not chunk_data_list:
            return []

        texts = [item['content'] for item in chunk_data_list]
        vectors = generate_embeddings(texts)

        faiss.normalize_L2(vectors)

        start_idx = self.index.ntotal
        self.index.add(vectors)

        assigned_embedding_ids = []
        for offset, item in enumerate(chunk_data_list):
            faiss_id = start_idx + offset
            assigned_embedding_ids.append(faiss_id)
            self.metadata[str(faiss_id)] = {
                'chunk_id': item['chunk_id'],
                'document_id': item['document_id'],
                'url': item['url'],
                'title': item['title'],
                'chunk_index': item['chunk_index'],
                'content': item['content']
            }

        self.save()
        return assigned_embedding_ids

    def search(self, query: str, top_k: int = 5, score_threshold: float = 0.25) -> list[dict]:
        """
        Performs semantic search for a query string.
        Returns top-K matching chunk items with scores.
        """
        if not self.index or self.index.ntotal == 0:
            return []

        query_vector = generate_embeddings([query])
        faiss.normalize_L2(query_vector)

        distances, indices = self.index.search(query_vector, min(top_k, self.index.ntotal))

        results = []
        for score, idx in zip(distances[0], indices[0]):
            if idx == -1:
                continue
            if score < score_threshold:
                continue
            
            meta = self.metadata.get(str(idx), {})
            if meta:
                results.append({
                    'score': float(score),
                    'embedding_id': int(idx),
                    'chunk_id': meta.get('chunk_id'),
                    'document_id': meta.get('document_id'),
                    'url': meta.get('url'),
                    'title': meta.get('title'),
                    'chunk_index': meta.get('chunk_index'),
                    'content': meta.get('content', '')
                })

        return results

    def reset(self):
        """Clears index and metadata."""
        self._init_fresh_index()
        self.save()


_VECTOR_STORE = None

def get_vector_store() -> FAISSVectorStore:
    global _VECTOR_STORE
    if _VECTOR_STORE is None:
        _VECTOR_STORE = FAISSVectorStore()
    return _VECTOR_STORE
