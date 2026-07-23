import re


def _split_long_text(text: str, max_chars: int) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        if len(sentence) > max_chars:
            if current:
                chunks.append(current)
                current = ""
            words = sentence.split()
            window = ""
            for word in words:
                if len(word) > max_chars:
                    if window:
                        chunks.append(window)
                        window = ""
                    chunks.extend(
                        word[start : start + max_chars]
                        for start in range(0, len(word), max_chars)
                    )
                    continue
                candidate = f"{window} {word}".strip()
                if window and len(candidate) > max_chars:
                    chunks.append(window)
                    window = word
                else:
                    window = candidate
            if window:
                chunks.append(window)
            continue

        candidate = f"{current} {sentence}".strip()
        if current and len(candidate) > max_chars:
            chunks.append(current)
            current = sentence
        else:
            current = candidate

    if current:
        chunks.append(current)
    return chunks


def chunk_document(
    text: str,
    max_chars: int = 900,
    overlap_chars: int = 120,
) -> list[str]:
    if max_chars < 100:
        raise ValueError("max_chars must be at least 100")
    if overlap_chars < 0 or overlap_chars >= max_chars:
        raise ValueError("overlap_chars must be between 0 and max_chars")

    normalized = text.replace("\r\n", "\n").strip()
    if not normalized:
        return []

    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", normalized) if part.strip()]
    sections: list[str] = []
    for paragraph in paragraphs:
        if len(paragraph) <= max_chars:
            sections.append(paragraph)
        else:
            sections.extend(_split_long_text(paragraph, max_chars))

    chunks: list[str] = []
    current = ""
    for section in sections:
        candidate = f"{current}\n\n{section}".strip()
        if current and len(candidate) > max_chars:
            chunks.append(current)
            overlap = current[-overlap_chars:].lstrip() if overlap_chars else ""
            current = f"{overlap}\n\n{section}".strip()
            if len(current) > max_chars:
                split_current = _split_long_text(current, max_chars)
                chunks.extend(split_current[:-1])
                current = split_current[-1]
        else:
            current = candidate

    if current:
        chunks.append(current)
    return chunks
