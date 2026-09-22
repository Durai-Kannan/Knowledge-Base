import numpy as np
from sentence_transformers import SentenceTransformer

_EMBEDDING_MODEL = None
MODEL_NAME = 'all-MiniLM-L6-v2'

def get_embedding_model() -> SentenceTransformer:
    global _EMBEDDING_MODEL
    if _EMBEDDING_MODEL is None:
        _EMBEDDING_MODEL = SentenceTransformer(MODEL_NAME)
    return _EMBEDDING_MODEL


def generate_embeddings(texts: list[str]) -> np.ndarray:
    """
    Generates normalized 384-dimensional vector embeddings for a list of strings.
    Returns float32 numpy array.
    """
    if not texts:
        return np.empty((0, 384), dtype=np.float32)

    model = get_embedding_model()
    embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
    return embeddings.astype(np.float32)
