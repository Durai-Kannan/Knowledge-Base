import re
from typing import List

def chunk_text(text: str, chunk_size: int = 700, chunk_overlap: int = 100) -> List[str]:
    """
    Splits text into overlapping chunks while preserving sentence boundaries when feasible.
    """
    if not text or not text.strip():
        return []

    # If text is smaller than chunk_size, return it as a single chunk
    if len(text) <= chunk_size:
        return [text]

    # Split text by sentence endings
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    chunks = []
    current_chunk = []
    current_length = 0

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        sentence_len = len(sentence)

        if current_length + sentence_len > chunk_size and current_chunk:
            # Join current chunk
            chunk_str = " ".join(current_chunk)
            chunks.append(chunk_str)

            # Keep overlap for next chunk
            overlap_length = 0
            overlap_chunk = []

            for s in reversed(current_chunk):
                if overlap_length + len(s) <= chunk_overlap:
                    overlap_chunk.insert(0, s)
                    overlap_length += len(s)
                else:
                    break

            current_chunk = overlap_chunk
            current_length = sum(len(s) for s in current_chunk)

        current_chunk.append(sentence)
        current_length += sentence_len

    if current_chunk:
        chunk_str = " ".join(current_chunk)
        if not chunks or chunk_str != chunks[-1]:
            chunks.append(chunk_str)

    return chunks
