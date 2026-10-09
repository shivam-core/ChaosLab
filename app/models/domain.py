from datetime import datetime
import uuid
from typing import List, Optional, Dict, Any

from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, JSON, Boolean, BigInteger
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    token_digest: Mapped[str] = mapped_column(String, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    quota_bytes_used: Mapped[int] = mapped_column(BigInteger, default=0)


class Upload(Base):
    __tablename__ = "uploads"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    original_name: Mapped[str] = mapped_column(String)
    mime_type: Mapped[str] = mapped_column(String)
    byte_count: Mapped[int] = mapped_column(BigInteger)
    sha256_hash: Mapped[str] = mapped_column(String)
    raw_bytes: Mapped[bytes] = mapped_column(deferred=True)  # Store file content
    status: Mapped[str] = mapped_column(String) # uploaded, parsing, needs_review, ready, rejected
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String)
    currency: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    coverage_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    coverage_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    dataset_hash: Mapped[str] = mapped_column(String)
    summary: Mapped[Dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    transactions: Mapped[List["Transaction"]] = relationship(back_populates="dataset", cascade="all, delete-orphan")


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id: Mapped[str] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"), index=True)
    source_row_id: Mapped[str] = mapped_column(String, index=True)
    transaction_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    product_id: Mapped[str] = mapped_column(String, index=True)
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price_minor: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    order_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    product_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    provenance: Mapped[Dict[str, Any]] = mapped_column(JSON)

    dataset: Mapped["Dataset"] = relationship(back_populates="transactions")


class Scenario(Base):
    __tablename__ = "scenarios"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    dataset_id: Mapped[str] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String)
    config_json: Mapped[Dict[str, Any]] = mapped_column(JSON)
    config_hash: Mapped[str] = mapped_column(String)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Job(Base):
    """PostgreSQL durable job queue table for worker tasks."""
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    kind: Mapped[str] = mapped_column(String, index=True) # "parse", "run", "pdf"
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    resource_id: Mapped[Optional[str]] = mapped_column(String, nullable=True) # upload_id, run_id, report_id
    status: Mapped[str] = mapped_column(String, default="queued", index=True) # queued, running, succeeded, failed, cancelled
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    lease_token: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    lease_expiry: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    progress: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    safe_error: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    scenario_id: Mapped[str] = mapped_column(ForeignKey("scenarios.id"), index=True)
    job_id: Mapped[Optional[str]] = mapped_column(ForeignKey("jobs.id"), nullable=True)
    engine_version: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="queued")
    summary: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    results: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    comparison_hash: Mapped[str] = mapped_column(String)
    pdf_bytes: Mapped[Optional[bytes]] = mapped_column(deferred=True, nullable=True)
    byte_count: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    status: Mapped[str] = mapped_column(String, default="generating")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
