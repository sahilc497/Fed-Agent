from typing import List, Dict, Any


def chunk_text(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    page_number: int = 1
) -> List[Dict[str, Any]]:
    """
    Splits text into overlapping chunks, preserving character boundaries and page numbers.
    """
    words = text.split()
    if not words:
        return []

    chunks = []
    chunk_index = 0
    start = 0

    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk_words = words[start:end]
        chunk_content = " ".join(chunk_words)

        chunks.append({
            "chunk_index": chunk_index,
            "content": chunk_content,
            "page_number": page_number
        })

        chunk_index += 1
        if end == len(words):
            break
        start += (chunk_size - chunk_overlap)

    return chunks
