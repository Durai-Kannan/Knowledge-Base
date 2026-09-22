import pytest
from vector_store.faiss_store import FAISSVectorStore

def test_faiss_vector_store_add_and_search():
    store = FAISSVectorStore()
    store.reset()

    sample_chunks = [
        {
            'chunk_id': 101,
            'document_id': 1,
            'url': 'https://example.com/exec/ceo',
            'title': 'CEO Bio',
            'chunk_index': 0,
            'content': 'John Smith serves as Chief Executive Officer overseeing cloud infrastructure and product strategy.'
        },
        {
            'chunk_id': 102,
            'document_id': 2,
            'url': 'https://example.com/exec/cto',
            'title': 'CTO Bio',
            'chunk_index': 0,
            'content': 'Alice Johnson is Chief Technology Officer driving artificial intelligence R&D and deep learning initiatives.'
        }
    ]

    faiss_ids = store.add_chunks(sample_chunks)
    assert len(faiss_ids) == 2

    results = store.search("artificial intelligence R&D", top_k=2, score_threshold=0.1)
    assert len(results) > 0
    top_result = results[0]
    assert top_result['chunk_id'] == 102
    assert 'Alice Johnson' in top_result['content']
