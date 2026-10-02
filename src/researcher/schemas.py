from pydantic import BaseModel, Field

class ResearchProjectCreate(BaseModel):
    title: str
    question: str
    scope: str | None = None

class SearchRequest(BaseModel):
    query: str
    max_results: int = Field(default=20, ge=1, le=100)

class SourceRecord(BaseModel):
    title: str
    doi: str | None = None
    year: int | None = None
    venue: str | None = None
    url: str | None = None
    source: str

class Claim(BaseModel):
    text: str
    claim_type: str = "atomic"

class GapCandidate(BaseModel):
    statement: str
    classification: str
    evidence_ids: list[str] = []

class PlanRequest(BaseModel):
    question: str

class OrchestratorUpdate(BaseModel):
    evidence_count: int = Field(ge=0)
    coverage_score: float = Field(ge=0, le=1)
    disagreements: int = Field(default=0, ge=0)

class RunQuery(BaseModel):
    query: str
    max_results: int = Field(default=20, ge=1, le=100)
