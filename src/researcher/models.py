from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

class Base(DeclarativeBase):
    pass

class Project(Base):
    __tablename__ = "projects"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(500))
    question: Mapped[str] = mapped_column(Text)
    scope: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    sources: Mapped[list["Source"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    claims: Mapped[list["Claim"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    runs: Mapped[list["ResearchRun"]] = relationship(back_populates="project", cascade="all, delete-orphan")

class Source(Base):
    __tablename__ = "sources"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    title: Mapped[str] = mapped_column(Text)
    doi: Mapped[Optional[str]] = mapped_column(String(300), nullable=True, index=True)
    year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    venue: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    provider: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    project: Mapped["Project"] = relationship(back_populates="sources")
    passages: Mapped[list["Passage"]] = relationship(back_populates="source", cascade="all, delete-orphan")
    __table_args__ = (UniqueConstraint("project_id", "doi", name="uq_project_source_doi"),)

class Passage(Base):
    __tablename__ = "passages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"))
    locator: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    text: Mapped[str] = mapped_column(Text)
    source: Mapped["Source"] = relationship(back_populates="passages")
    evidence_links: Mapped[list["EvidenceLink"]] = relationship(back_populates="passage", cascade="all, delete-orphan")

class Claim(Base):
    __tablename__ = "claims"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    text: Mapped[str] = mapped_column(Text)
    claim_type: Mapped[str] = mapped_column(String(100), default="atomic")
    status: Mapped[str] = mapped_column(String(50), default="unverified")
    project: Mapped["Project"] = relationship(back_populates="claims")
    evidence_links: Mapped[list["EvidenceLink"]] = relationship(back_populates="claim", cascade="all, delete-orphan")

class EvidenceLink(Base):
    __tablename__ = "evidence_links"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    claim_id: Mapped[int] = mapped_column(ForeignKey("claims.id"))
    passage_id: Mapped[int] = mapped_column(ForeignKey("passages.id"))
    relation: Mapped[str] = mapped_column(String(50), default="supports")
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    claim: Mapped["Claim"] = relationship(back_populates="evidence_links")
    passage: Mapped["Passage"] = relationship(back_populates="evidence_links")

class ResearchRun(Base):
    __tablename__ = "research_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    status: Mapped[str] = mapped_column(String(50), default="created")
    coverage_score: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    project: Mapped["Project"] = relationship(back_populates="runs")
    tasks: Mapped[list["ResearchTask"]] = relationship(back_populates="run", cascade="all, delete-orphan")

class ResearchTask(Base):
    __tablename__ = "research_tasks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("research_runs.id"))
    role: Mapped[str] = mapped_column(String(80))
    objective: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    priority: Mapped[int] = mapped_column(Integer, default=100)
    run: Mapped["ResearchRun"] = relationship(back_populates="tasks")

class VerificationEvent(Base):
    __tablename__ = "verification_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    claim_id: Mapped[int] = mapped_column(ForeignKey("claims.id"))
    status: Mapped[str] = mapped_column(String(80))
    reason: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class GapDossier(Base):
    __tablename__ = "gap_dossiers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    statement: Mapped[str] = mapped_column(Text)
    classification: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(50), default="candidate")
    rationale: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
