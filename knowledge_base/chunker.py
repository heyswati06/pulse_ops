def chunk_text(text: str, chunk_size: int = 300, overlap: int = 50) -> list:
    """
    Split long text into overlapping chunks of ~chunk_size words.

    Why overlap? So a fix that spans two chunks isn't cut in half.

    Args:
        text       : Raw plain text to chunk
        chunk_size : Target words per chunk (default 300)
        overlap    : Words to repeat between chunks (default 50)

    Returns:
        List of text strings, each ~chunk_size words
    """
    words  = text.split()
    chunks = []
    start  = 0

    while start < len(words):
        end   = start + chunk_size
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk.strip())
        start = end - overlap  # overlap keeps context across boundaries

    return chunks


def clean_text(raw: str) -> str:
    """
    Basic cleanup — remove excessive whitespace, empty lines, control chars.
    Call this before chunking.
    """
    lines = raw.splitlines()
    lines = [line.strip() for line in lines if line.strip()]
    return "\n".join(lines)
