from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

@dataclass(frozen=True)
class EvidenceRecord:
    id: str
    claim_id: str
    passage_id: str
    relation: str
    confidence: float
    created_at: datetime

class EvidenceStore:
    """Application-level evidence store.

    The MVP keeps the service interface independent from the database layer.
    A PostgreSQL repository can implement the same operations without changing
    agents or verification logic.
    """

    def __init__(self) -> None:
        self._records: dict[str, EvidenceRecord] = {}

    def link(self, claim_id: str, passage_id: str, relation: str = "supports",
             confidence: float = 1.0) -> EvidenceRecord:
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        record = EvidenceRecord(
            id=str(uuid4()),
            claim_id=claim_id,
            passage_id=passage_id,
            relation=relation,
            confidence=confidence,
            created_at=datetime.now(timezone.utc),
        )
        self._records[record.id] = record
        return record

    def for_claim(self, claim_id: str) -> list[EvidenceRecord]:
        return [r for r in self._records.values() if r.claim_id == claim_id]
