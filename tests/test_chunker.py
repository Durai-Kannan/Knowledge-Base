import pytest
from ingestion.chunker import chunk_text

def test_chunk_text_short():
    short_text = "This is a short text under 700 characters."
    chunks = chunk_text(short_text, chunk_size=700, chunk_overlap=100)
    assert len(chunks) == 1
    assert chunks[0] == short_text

def test_chunk_text_long_sentence_splitting():
    sentences = [f"Sentence number {i} provides detailed contextual background." for i in range(30)]
    long_text = " ".join(sentences)
    chunks = chunk_text(long_text, chunk_size=300, chunk_overlap=50)
    
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) <= 500  # Should split reasonably around sentence boundaries
