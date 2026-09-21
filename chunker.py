"""
Stage 2 of the pipeline: splitting documents into chunks.

⚠️ THIS IS THE FILE YOU CHANGE IN MILESTONE 3.

`split_documents` below is deliberately plain. It cuts every document into
fixed-size pieces with a fixed overlap and pays no attention to where sentences
or paragraphs end. It works, and it is not good.

On a corpus of short posts it may not cut anything at all: `campus_life` comes
out as 88 documents and 88 chunks, because almost nothing in it reaches 800
characters. That is the baseline, not a bug — Milestone 3 is where you decide
whether one post should stay one chunk.

Your job in Milestone 3 is to replace the *body* of `split_documents` with a
strategy that fits the documents you actually read in Milestone 1. Keep the
name and the shape of what it returns — the rest of the pipeline calls it, and
your README has to name the function that produced your chunks.

If you get stuck for 30 minutes, `fallback_split` is the original. Switch back
to it, write down what you saw, and move on. That's a real observation about
your pipeline, not giving up.
"""

import re
from dataclasses import dataclass

import config
from ingest import Document


@dataclass
class Chunk:
    """One piece of one document."""

    text: str
    source: str        # which file it came from
    index: int         # which chunk within that file, starting at 0
    produced_by: str   # the function that made it — cite this in your README

    @property
    def label(self) -> str:
        return f"{self.source}#{self.index}"


def fallback_split(
    documents: list[Document],
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> list[Chunk]:
    """
    The starter's original chunker. Fixed-size character windows with overlap.

    Keep this function. Milestone 3's stop rule points back at it, and having
    something to compare your own strategy against is useful in unit 2.
    """
    chunk_size = chunk_size or config.CHUNK_SIZE
    overlap = overlap or config.CHUNK_OVERLAP

    if overlap >= chunk_size:
        raise ValueError("overlap has to be smaller than chunk_size")

    chunks: list[Chunk] = []
    for doc in documents:
        start = 0
        index = 0
        while start < len(doc.text):
            piece = doc.text[start : start + chunk_size].strip()
            if piece:
                chunks.append(
                    Chunk(
                        text=piece,
                        source=doc.source,
                        index=index,
                        produced_by="chunker.py::fallback_split",
                    )
                )
                index += 1
            start += chunk_size - overlap

    return chunks


def _sections(text: str) -> list[tuple[str, str]]:
    """
    Break one guide into (header, body) pairs on its `##` headings.

    These documents come with the structure already in them: a `# Town` title
    at the top and `## Getting there`, `## Eat and drink`, `## When to go`
    under it. Cutting anywhere else throws that away.

    The header comes back as "Kestrelford — Eat and drink" so it can be put
    at the top of the chunk text. Nine of the fourteen guides have a section
    called "Eat and drink", so a chunk that doesn't carry its town name is
    indistinguishable from eight others once it's a vector.
    """
    title = ""
    heading = "Overview"
    body: list[str] = []
    out: list[tuple[str, str]] = []

    def flush() -> None:
        joined = "\n".join(body).strip()
        if joined:
            out.append((f"{title} — {heading}" if title else heading, joined))
        body.clear()

    for line in text.split("\n"):
        if line.startswith("## "):
            flush()
            heading = line[3:].strip()
        elif line.startswith("# "):
            flush()
            title = line[2:].strip()
            heading = "Overview"
        else:
            body.append(line)
    flush()

    return out


def _split_long(body: str, max_chars: int, overlap: int) -> list[str]:
    """
    Split one over-long section at sentence boundaries, not mid-word.

    As it turns out, no section in city_guides reaches 900 characters — the
    longest is 691 — so on this corpus this function never actually fires and
    CHUNK_OVERLAP never gets used. It stays in because the 1,200 ceiling in
    criterion 4 has to hold for any document, and a guide with one long
    unbroken section would otherwise break it. When it does fire, the tail of
    the previous piece is carried into the next so a sentence that straddles
    the cut is whole in at least one of them.
    """
    if len(body) <= max_chars:
        return [body]

    # Sentence-ish: split after . ! ? followed by whitespace.
    sentences = re.split(r"(?<=[.!?])\s+", body)
    pieces: list[str] = []
    current = ""

    for sentence in sentences:
        if current and len(current) + 1 + len(sentence) > max_chars:
            pieces.append(current.strip())
            tail = current[-overlap:]
            # Start the carried-over text at a sentence boundary if there is one.
            cut = re.search(r"(?<=[.!?])\s+", tail)
            current = (tail[cut.end():] if cut else "") + " " + sentence
        else:
            current = f"{current} {sentence}".strip()

    if current.strip():
        pieces.append(current.strip())

    return pieces


def _merge_short(pieces: list[str], min_chars: int, ceiling: int) -> list[str]:
    """
    Glue any piece under `min_chars` onto a neighbour inside the same document.

    The starter left a 24-character chunk on this corpus — the tail of a
    document that didn't divide evenly into 800s. A chunk that small is a
    fragment: it embeds to nothing useful and it can only ever be noise in a
    result list. Merging forward keeps it attached to the text it belongs to.
    """
    merged: list[str] = []
    for piece in pieces:
        if merged and len(piece) < min_chars and len(merged[-1]) + len(piece) + 2 <= ceiling:
            merged[-1] = f"{merged[-1]}\n\n{piece}"
        else:
            merged.append(piece)

    # A short *first* section has no previous neighbour, so fold it forward.
    if len(merged) > 1 and len(merged[0]) < min_chars and len(merged[0]) + len(merged[1]) + 2 <= ceiling:
        merged[1] = f"{merged[0]}\n\n{merged[1]}"
        merged.pop(0)

    return merged


def split_documents(documents: list[Document]) -> list[Chunk]:
    """
    Split documents on the headings they already carry. ← Milestone 3.

    One `##` section is one chunk, with the town name and the heading kept at
    the top of the chunk text. Sections over CHUNK_SIZE get split further at
    sentence boundaries with CHUNK_OVERLAP characters carried across; sections
    under CHUNK_MIN get merged into the neighbour they belong to.

    Why this and not a character window: these guides are 1,400 to 2,500
    characters of labelled sections, and the answer to a real question —
    "when does the bakery sell out", "when does the car park fill" — sits
    inside one section. An 800-character window cuts across those boundaries,
    so a chunk routinely ends halfway through "Eat and drink" and begins
    halfway through "What to see". Splitting on the structure the author
    already put there keeps each chunk about one topic in one town.
    """
    max_chars = config.CHUNK_SIZE
    overlap = config.CHUNK_OVERLAP
    min_chars = config.CHUNK_MIN
    ceiling = 1200          # criterion 4's upper bound, enforced here

    chunks: list[Chunk] = []
    for doc in documents:
        pieces: list[str] = []
        for header, body in _sections(doc.text):
            for part in _split_long(body, max_chars, overlap):
                pieces.append(f"{header}\n\n{part}")

        for index, text in enumerate(_merge_short(pieces, min_chars, ceiling)):
            chunks.append(
                Chunk(
                    text=text,
                    source=doc.source,
                    index=index,
                    produced_by="chunker.py::split_documents",
                )
            )

    return chunks


def describe(chunks: list[Chunk]) -> str:
    """A one-line summary, printed after indexing."""
    if not chunks:
        return "0 chunks"
    lengths = [len(c.text) for c in chunks]
    return (
        f"{len(chunks)} chunks, "
        f"{sum(lengths) // len(lengths)} characters on average "
        f"(shortest {min(lengths)}, longest {max(lengths)}), "
        f"produced by {chunks[0].produced_by}"
    )


if __name__ == "__main__":
    from ingest import load_documents

    chunks = split_documents(load_documents())
    print(describe(chunks))
