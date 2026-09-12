import re


def split_into_sentences(text: str) -> list[str]:

    text = text.strip()

    if not text:
        return []

    sentences = re.split(
        r'(?<=[.!?])\s+',
        text
    )

    return [
        sentence.strip()
        for sentence in sentences
        if sentence.strip()
    ]


def split_into_chunks(
    text: str,
    max_chunk_size: int = 700,
    overlap_sentences: int = 1
) -> list[str]:

    sentences = split_into_sentences(text)

    chunks = []
    current_sentences = []
    current_length = 0

    for sentence in sentences:

        sentence_length = len(sentence)

        if (
            current_sentences
            and current_length + sentence_length > max_chunk_size
        ):

            chunks.append(
                " ".join(current_sentences)
            )

            if overlap_sentences > 0:
                current_sentences = current_sentences[-overlap_sentences:]
                current_length = sum(
                    len(item)
                    for item in current_sentences
                )
            else:
                current_sentences = []
                current_length = 0

        current_sentences.append(sentence)
        current_length += sentence_length

    if current_sentences:
        chunks.append(
            " ".join(current_sentences)
        )

    return chunks