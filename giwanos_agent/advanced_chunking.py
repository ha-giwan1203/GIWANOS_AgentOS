
def advanced_chunk_text(text, max_chunk_size=700, overlap=100):
    import re
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks, current_chunk = [], ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= max_chunk_size:
            current_chunk += sentence + " "
        else:
            chunks.append(current_chunk.strip())
            current_chunk = current_chunk[-overlap:] + sentence + " "
    
    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks
