from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Claim, EvidenceLink, GapDossier, Passage, Project, ResearchRun, ResearchTask, Source, VerificationEvent


class Repository:
    def __init__(self, session: Session):
        self.session = session

    def create_project(self, title: str, question: str, scope: str | None = None) -> Project:
        project = Project(title=title, question=question, scope=scope)
        self.session.add(project)
        self.session.flush()
        return project

    def get_project(self, project_id: int) -> Project | None:
        return self.session.get(Project, project_id)

    def create_run(self, project_id: int) -> ResearchRun:
        run = ResearchRun(project_id=project_id)
        self.session.add(run)
        self.session.flush()
        return run

    def get_run(self, run_id: int) -> ResearchRun | None:
        return self.session.get(ResearchRun, run_id)

    def add_task(self, run_id: int, role: str, objective: str, priority: int = 100) -> ResearchTask:
        task = ResearchTask(run_id=run_id, role=role, objective=objective, priority=priority)
        self.session.add(task)
        self.session.flush()
        return task

    def list_tasks(self, run_id: int) -> list[ResearchTask]:
        return list(self.session.scalars(
            select(ResearchTask).where(ResearchTask.run_id == run_id).order_by(ResearchTask.priority)
        ))

    def add_source(self, project_id: int, title: str, provider: str, doi: str | None = None,
                   year: int | None = None, venue: str | None = None,
                   url: str | None = None) -> Source:
        source = Source(project_id=project_id, title=title, provider=provider, doi=doi,
                        year=year, venue=venue, url=url)
        self.session.add(source)
        self.session.flush()
        return source

    def add_passage(self, source_id: int, text: str, locator: str | None = None) -> Passage:
        passage = Passage(source_id=source_id, text=text, locator=locator)
        self.session.add(passage)
        self.session.flush()
        return passage

    def add_claim(self, project_id: int, text: str, claim_type: str = "atomic") -> Claim:
        claim = Claim(project_id=project_id, text=text, claim_type=claim_type)
        self.session.add(claim)
        self.session.flush()
        return claim

    def link_evidence(self, claim_id: int, passage_id: int, relation: str = "supports",
                      confidence: float | None = None) -> EvidenceLink:
        link = EvidenceLink(claim_id=claim_id, passage_id=passage_id,
                            relation=relation, confidence=confidence)
        self.session.add(link)
        self.session.flush()
        return link

    def add_verification(self, claim_id: int, status: str, reason: str) -> VerificationEvent:
        event = VerificationEvent(claim_id=claim_id, status=status, reason=reason)
        self.session.add(event)
        self.session.flush()
        return event

    def add_gap(self, project_id: int, statement: str, classification: str,
                rationale: str | None = None) -> GapDossier:
        gap = GapDossier(project_id=project_id, statement=statement,
                         classification=classification, rationale=rationale)
        self.session.add(gap)
        self.session.flush()
        return gap

    def list_sources(self, project_id: int) -> list[Source]:
        return list(self.session.scalars(
            select(Source).where(Source.project_id == project_id).order_by(Source.year.desc())
        ))

    def list_claims(self, project_id: int) -> list[Claim]:
        return list(self.session.scalars(
            select(Claim).where(Claim.project_id == project_id).order_by(Claim.id)
        ))

    def list_gaps(self, project_id: int) -> list[GapDossier]:
        return list(self.session.scalars(
            select(GapDossier).where(GapDossier.project_id == project_id).order_by(GapDossier.id)
        ))

    def commit(self) -> None:
        self.session.commit()
