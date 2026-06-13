import logging
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from .load_documents import load_documents
from collections import Counter

# Cap chunk size after header splitting so large sections don't produce a single
# oversized (and semantically diluted) embedding. Overlap preserves context
# across the boundaries.
MAX_CHUNK_CHARS = 1000
CHUNK_OVERLAP_CHARS = 150

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)




# Step2: Split the loaded and parsed document into chunks
def split_docs_chunks():
    """Splits documents into chunks. or example, a markdown file is organized by headers.
    Creating chunks within specific header groups is an intuitive idea.
    To address this challenge, we can use MarkdownHeaderTextSplitter.
    This will split a markdown file by a specified set of headers."""

    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
        ("####", "Header 4")
    ]

    docs = load_documents()

    all_chunks = []
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on, strip_headers=True)
    char_splitter = RecursiveCharacterTextSplitter(
        chunk_size=MAX_CHUNK_CHARS,
        chunk_overlap=CHUNK_OVERLAP_CHARS,
    )

    for doc in docs:
        base_metadata = dict(doc.metadata or {})
        md_header_splits = markdown_splitter.split_text(doc.page_content)

        header_sizes = [len(c.page_content) for c in md_header_splits]
        logger.info(
            "[chunking pre-cap] source=%s header_chunks=%d max=%d top_sizes=%s",
            base_metadata.get("source"),
            len(md_header_splits),
            max(header_sizes) if header_sizes else 0,
            sorted(header_sizes, reverse=True)[:5],
        )

        for chunk in md_header_splits:
            chunk_metadata = dict(chunk.metadata or {})

            chunk.metadata = {
                **base_metadata,
                **chunk_metadata,
                "department": base_metadata.get("department", "general")
            }

        all_chunks.extend(md_header_splits)

    # Second pass: bound chunk sizes (metadata is preserved across sub-splits).
    all_chunks = char_splitter.split_documents(all_chunks)

    # Post-cap summary across all documents.
    final_sizes = [len(c.page_content) for c in all_chunks]
    if final_sizes:
        logger.info(
            "[chunking post-cap] total_chunks=%d min=%d max=%d avg=%d by_department=%s",
            len(all_chunks),
            min(final_sizes),
            max(final_sizes),
            sum(final_sizes) // len(final_sizes),
            dict(Counter(c.metadata.get("department") for c in all_chunks)),
        )

    return all_chunks





