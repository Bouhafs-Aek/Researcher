from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from .documents import DocumentAcquirer, extract_pdf_pages
from .repository import Repository
from .retrieval import MultiSourceRetriever


@dataclass
class PipelineResult:
    run_id: int
    retrieved: int
    stored: int


@dataclass
class DocumentIngestResult:
    attempted: int
    extracted: int
    passages: int
    skipped: int
    errors: list[str]


class ResearchPipeline:
    """Deterministic ingestion stages.

    Bibliographic metadata never becomes scientific evidence by itself.
    Full-text passages are stored with source-version provenance, and claim
    extraction remains an explicit downstream operation.
    """

    def __init__(
        self,
        retriever: MultiSourceRetriever | None = None,
        acquirer: DocumentAcquirer | None = None,
    ) -> None:
        self.retriever = retriever or MultiSourceRetriever()
        self.acquirer = acquirer or DocumentAcquirer()

    async def retrieve_and_ingest(
        self, session: Session, project_id: int, run_id: int, query: str,
        max_results: int = 20,
    ) -> PipelineResult:
        repo = Repository(session)
        records = await self.retriever.search(query, max_results)
        stored = 0
        existing = {source.doi for source in repo.list_sources(project_id) if source.doi}

        for record in records:
            if record.doi and record.doi in existing:
                continue
            repo.add_source(
                project_id=project_id, title=record.title, provider=record.source,
                doi=record.doi, year=record.year, venue=record.venue, url=record.url,
            )
            stored += 1

        run = repo.get_run(run_id)
        if run is not None:
            run.status = "retrieved"
            run.coverage_score = min(1.0, stored / max(1, max_results))

        session.commit()
        return PipelineResult(run_id=run_id, retrieved=len(records), stored=stored)

    async def acquire_documents(
        self, session: Session, project_id: int, run_id: int,
        source_ids: list[int] | None = None, max_documents: int = 20,
    ) -> DocumentIngestResult:
        repo = Repository(session)
        sources = repo.list_sources(project_id)
        if source_ids is not None:
            wanted = set(source_ids)
            sources = [s for s in sources if s.id in wanted]
        sources = sources[:max_documents]

        attempted = extracted = passage_count = skipped = 0
        errors: list[str] = []

        for source in sources:
            attempted += 1
            if not DocumentAcquirer.is_candidate_url(source.url):
                skipped += 1
                continue
            try:
                document = await self.acquirer.fetch(source.url)
                version = repo.add_source_version(
                    source.id, document.content_type, document.url, document.sha256, "extracted"
                )
                pages = extract_pdf_pages(document.content)
                for page_number, text in pages:
                    repo.add_passage(source.id, text, f"page:{page_number};version:{version.id}")
                    passage_count += 1
                extracted += 1
            except Exception as exc:
                errors.append(f"source {source.id}: {type(exc).__name__}: {exc}")

        run = repo.get_run(run_id)
        if run is not None:
            run.status = "documents_ingested"
        session.commit()
        return DocumentIngestResult(
            attempted=attempted, extracted=extracted, passages=passage_count,
            skipped=skipped, errors=errors,
        )
