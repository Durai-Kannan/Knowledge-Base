from .faiss_store import get_vector_store

def perform_vector_search(query: str, top_k: int = 5, score_threshold: float = 0.20) -> list[dict]:
    """
    High level semantic search helper function.
    """
    store = get_vector_store()
    return store.search(query, top_k=top_k, score_threshold=score_threshold)
