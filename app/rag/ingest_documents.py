import hashlib
import logging

from sqlalchemy import select

from app.database.session import SessionLocal
from app.models.document_chunk_model import DocumentChunkDB
from app.rag.embeddings import embed_documents
from app.rag.split_documents import split_docs_chunks


logger = logging.getLogger(__name__)

BATCH_SIZE = 100


def calculate_hash(text: str) -> str:
    return hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()


def ingest_documents():
    chunks = split_docs_chunks()

    if not chunks:
        raise ValueError(
            "No chunks were generated."
        )

    db = SessionLocal()

    inserted = 0
    skipped = 0

    try:
        for start in range(
            0,
            len(chunks),
            BATCH_SIZE,
        ):
            batch = chunks[
                start:start + BATCH_SIZE
            ]

            texts = [
                chunk.page_content
                for chunk in batch
            ]

            vectors = embed_documents(texts)

            for offset, (
                chunk,
                vector,
            ) in enumerate(
                zip(batch, vectors)
            ):
                metadata = (
                    chunk.metadata or {}
                )

                source = metadata.get(
                    "source",
                    "unknown"
                )

                path = metadata.get(
                    "path"
                )

                department = metadata.get(
                    "department",
                    "general"
                )

                content_hash = calculate_hash(
                    chunk.page_content
                )

                chunk_index = (
                    start + offset
                )

                document_id = (
                    path or source
                )

                existing = db.scalar(
                    select(
                        DocumentChunkDB
                    ).where(
                        DocumentChunkDB.document_id
                        == document_id,

                        DocumentChunkDB.chunk_index
                        == chunk_index,

                        DocumentChunkDB.content_hash
                        == content_hash,
                    )
                )

                if existing:
                    skipped += 1
                    continue

                row = DocumentChunkDB(
                    document_id=document_id,
                    source=source,
                    path=path,
                    department=department,
                    chunk_index=chunk_index,
                    content=chunk.page_content,
                    content_hash=content_hash,
                    chunk_metadata=metadata,
                    embedding=vector,
                )

                db.add(row)
                inserted += 1

            db.commit()

            logger.info(
                "Processed %s / %s chunks",
                min(
                    start + BATCH_SIZE,
                    len(chunks),
                ),
                len(chunks),
            )

        print(
            f"Ingestion complete. "
            f"Inserted={inserted}, "
            f"Skipped={skipped}"
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    ingest_documents()