from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from .repository import Repository
from .retrieval import MultiSourceRetriever


@dataclass
class PipelineResult:
    run_id: int
    retrieved: int
    stored: int


class ResearchPipeline:
    """Runs the deterministic ingestion stage of a research run.

    Claim extraction and verification remain explicit downstream stages; this
    service never invents claims from bibliographic metadata.
    """

    def __init__(self, retriever: MultiSourceRetriever | None = None) -> None:
        self.retriever = retriever or MultiSourceRetriever()

    async def retrieve_and_ingest(
        self, session: Session, project_id: int, run_id: int, query: str,
        max_results: int = 20,
    ) -> PipelineResult:
        repo = Repository(session)
        records = await self.retriever.search(query, max_results)

        stored = 0
        existing = {
            source.doi
            for source in repo.list_sources(project_id)
            if source.doi
        }

        for record in records:
            if record.doi and record.doi in existing:
                continue
            repo.add_source(
                project_id=project_id,
                title=record.title,
                provider=record.source,
                doi=record.doi,
                year=record.year,
                venue=record.venue,
                url=record.url,
            )
            stored += 1

        run = repo.get_run(run_id)
        if run is not None:
            run.status = "retrieved"
            run.coverage_score = min(1.0, stored / max(1, max_results))

        session.commit()
        return PipelineResult(run_id=run_id, retrieved=len(records), stored=stored)
