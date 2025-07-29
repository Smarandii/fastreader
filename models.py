"""Database models and utilities for the FastReader application.

The application uses SQLAlchemy's declarative base to define two tables:

* Pdf: stores metadata and extracted text for uploaded PDFs.
* ReadingLog: stores metadata about reading sessions for analytics/testing.

These models are designed with minimal fields because the application has
no user authentication; logs simply reference the PDF being read and
store session parameters.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()


class Pdf(Base):
    """Represents a PDF document uploaded by the user."""

    __tablename__ = "pdfs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    filepath = Column(String(1024), nullable=False)
    content = Column(Text, nullable=False)
    uploaded_at = Column(DateTime, default=_dt.datetime.utcnow, nullable=False)

    logs = relationship("ReadingLog", back_populates="pdf", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Pdf id={self.id} filename={self.filename}>"


class ReadingLog(Base):
    """Stores information about individual reading sessions."""

    __tablename__ = "reading_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pdf_id = Column(Integer, ForeignKey("pdfs.id"), nullable=False)
    started_at = Column(DateTime, default=_dt.datetime.utcnow, nullable=False)
    speed_wpm = Column(Integer, nullable=False)
    chunk_size = Column(Integer, nullable=False)
    duration_seconds = Column(Integer, nullable=True)

    pdf = relationship("Pdf", back_populates="logs")

    def __repr__(self) -> str:
        return (
            f"<ReadingLog id={self.id} pdf_id={self.pdf_id} speed_wpm={self.speed_wpm}"
            f" chunk_size={self.chunk_size}>"
        )


def init_engine(database_uri: str):
    """Create a new SQLAlchemy engine given a database URI."""
    return create_engine(database_uri)


def init_session_factory(engine):
    """Create a sessionmaker bound to the provided engine."""
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db(engine):
    """Create all tables in the database if they do not exist."""
    Base.metadata.create_all(engine)