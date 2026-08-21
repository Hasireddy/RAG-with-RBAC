from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from pgvector.sqlalchemy import VECTOR

from app.database.base import Base


EMBEDDING_DIMENSION = 1536


class DocumentChunkDB(Base):
    __tablename__ = "document_chunks"

    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    document_id = Column(
        String(500),
        nullable=False,
        index=True,
    )

    source = Column(
        String(500),
        nullable=False,
        index=True,
    )

    path = Column(
        String(1000),
        nullable=True,
    )

    department = Column(
        String(100),
        nullable=False,
        index=True,
    )

    chunk_index = Column(
        Integer,
        nullable=False,
    )

    content = Column(
        Text,
        nullable=False,
    )

    content_hash = Column(
        String(64),
        nullable=False,
        index=True,
    )

    chunk_metadata = Column(
        JSONB,
        nullable=False,
        default=dict,
    )

    embedding = Column(
        VECTOR(EMBEDDING_DIMENSION),
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    table_args = (
        UniqueConstraint(
            "document_id",
            "chunk_index",
            "content_hash",
            name="uq_document_chunk",
        ),
    )