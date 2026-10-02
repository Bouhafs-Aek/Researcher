from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from .agents import ResearchPlanner
from .config import settings
from .db import SessionLocal, init_db
from .evidence import verify_claim
from .models import Claim as ClaimModel, Passage, Project, Source
from .orchestrator import DynamicOrchestrator
from .pipeline import ResearchPipeline
from .reporting import build_html_report
from .repository import Repository
from .retrieval import MultiSourceRetriever
from .schemas import (
    ClaimCreate, ClaimVerify, DocumentIngestRequest, OrchestratorUpdate,
    PlanRequest, ResearchProjectCreate, RunQuery, SearchRequest,
)

app = FastAPI(title="Researcher", version="0.2.0")
orchestrator = DynamicOrchestrator()
retriever = MultiSourceRetriever()
pipeline = ResearchPipeline(retriever)


@app.on_event("startup")
def startup() -> None:
    if settings.app_env != "test":
        init_db()


@app.get("/dashboard")
def dashboard():
    return FileResponse("src/researcher/dashboard.html", media_type="text/html")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/projects")
def create_project(request: ResearchProjectCreate):
    session: Session = SessionLocal()
    try:
        project = Repository(session).create_project(request.title, request.question, request.scope)
        session.commit()
        return {"id": project.id, "title": project.title, "question": project.question}
    finally:
        session.close()


@app.post("/projects/{project_id}/runs")
def create_run(project_id: int):
    session: Session = SessionLocal()
    try:
        repo = Repository(session)
        project = repo.get_project(project_id)
        if project is None:
            raise HTTPException(status_code=404, detail="Project not found")
        run = repo.create_run(project_id)
        state = orchestrator.start(project.question)
        for item in state.tasks.values():
            repo.add_task(run.id, item.task.role.value, item.task.objective)
        session.commit()
        return {"run_id": run.id, "project_id": project_id, "status": run.status}
    finally:
        session.close()


@app.post("/runs/{run_id}/retrieve")
async def retrieve_run(run_id: int, request: RunQuery):
    session: Session = SessionLocal()
    try:
        repo = Repository(session)
        run = repo.get_run(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Run not found")
        result = await pipeline.retrieve_and_ingest(
            session, run.project_id, run_id, request.query, request.max_results
        )
        return {
            "run_id": result.run_id, "status": "retrieved",
            "retrieved": result.retrieved, "stored": result.stored,
        }
    except HTTPException:
        raise
    except Exception as exc:
        session.rollback()
        raise HTTPException(status_code=502, detail=f"Retrieval pipeline error: {exc}") from exc
    finally:
        session.close()


@app.post("/runs/{run_id}/documents")
async def ingest_documents(run_id: int, request: DocumentIngestRequest):
    session: Session = SessionLocal()
    try:
        repo = Repository(session)
        run = repo.get_run(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Run not found")
        result = await pipeline.acquire_documents(
            session, run.project_id, run_id, request.source_ids, request.max_documents
        )
        return result.__dict__
    except HTTPException:
        raise
    except Exception as exc:
        session.rollback()
        raise HTTPException(status_code=502, detail=f"Document ingestion error: {exc}") from exc
    finally:
        session.close()


@app.get("/runs/{run_id}")
def get_run(run_id: int):
    session: Session = SessionLocal()
    try:
        repo = Repository(session)
        run = repo.get_run(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Run not found")
        return {
            "id": run.id, "project_id": run.project_id, "status": run.status,
            "coverage_score": run.coverage_score,
            "tasks": [
                {"id": t.id, "role": t.role, "objective": t.objective, "status": t.status}
                for t in repo.list_tasks(run.id)
            ],
        }
    finally:
        session.close()


@app.get("/projects/{project_id}/evidence")
def get_evidence(project_id: int):
    session: Session = SessionLocal()
    try:
        repo = Repository(session)
        if repo.get_project(project_id) is None:
            raise HTTPException(status_code=404, detail="Project not found")
        return {
            "sources": [
                {
                    "id": s.id, "title": s.title, "doi": s.doi, "year": s.year,
                    "venue": s.venue, "url": s.url, "provider": s.provider,
                    "versions": [
                        {"id": v.id, "url": v.retrieval_url, "sha256": v.sha256, "status": v.status}
                        for v in repo.list_source_versions(s.id)
                    ],
                }
                for s in repo.list_sources(project_id)
            ],
            "claims": [
                {"id": c.id, "text": c.text, "claim_type": c.claim_type, "status": c.status}
                for c in repo.list_claims(project_id)
            ],
        }
    finally:
        session.close()


@app.get("/projects/{project_id}/sources/{source_id}/passages")
def get_passages(project_id: int, source_id: int):
    session: Session = SessionLocal()
    try:
        source = session.get(Source, source_id)
        if source is None or source.project_id != project_id:
            raise HTTPException(status_code=404, detail="Source not found")
        return [
            {"id": p.id, "locator": p.locator, "text": p.text}
            for p in Repository(session).list_passages(source_id)
        ]
    finally:
        session.close()


@app.post("/projects/{project_id}/claims")
def create_claim(project_id: int, request: ClaimCreate):
    session: Session = SessionLocal()
    try:
        repo = Repository(session)
        if repo.get_project(project_id) is None:
            raise HTTPException(status_code=404, detail="Project not found")
        passage = session.get(Passage, request.passage_id)
        if passage is None:
            raise HTTPException(status_code=404, detail="Passage not found")
        if passage.source.project_id != project_id:
            raise HTTPException(status_code=400, detail="Passage does not belong to project")
        claim = repo.add_claim(project_id, request.text, request.claim_type)
        repo.link_evidence(claim.id, passage.id, request.relation, request.confidence)
        session.commit()
        return {"id": claim.id, "status": claim.status, "passage_id": passage.id}
    finally:
        session.close()


@app.post("/projects/{project_id}/claims/{claim_id}/verify")
def verify_claim_endpoint(project_id: int, claim_id: int, request: ClaimVerify):
    session: Session = SessionLocal()
    try:
        repo = Repository(session)
        claim = session.get(ClaimModel, claim_id)
        if claim is None or claim.project_id != project_id:
            raise HTTPException(status_code=404, detail="Claim not found")
        decision = verify_claim(
            request.source_found, request.passage_found,
            request.interpretation_checked, request.counterevidence_checked,
        )
        repo.add_verification(claim_id, decision.status, decision.reason)
        session.commit()
        return {"claim_id": claim_id, "status": decision.status, "reason": decision.reason}
    finally:
        session.close()


@app.get("/projects/{project_id}/gaps")
def get_gaps(project_id: int):
    session: Session = SessionLocal()
    try:
        repo = Repository(session)
        if repo.get_project(project_id) is None:
            raise HTTPException(status_code=404, detail="Project not found")
        return [
            {"id": g.id, "statement": g.statement, "classification": g.classification,
             "status": g.status, "rationale": g.rationale}
            for g in repo.list_gaps(project_id)
        ]
    finally:
        session.close()


@app.get("/projects/{project_id}/report")
def get_report(project_id: int):
    session: Session = SessionLocal()
    try:
        if Repository(session).get_project(project_id) is None:
            raise HTTPException(status_code=404, detail="Project not found")
        return {"html": build_html_report(session, project_id)}
    finally:
        session.close()


@app.post("/search")
async def search(request: SearchRequest):
    try:
        records = await retriever.search(request.query, request.max_results)
        return {"count": len(records), "results": [r.model_dump() for r in records]}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Literature provider error: {exc}") from exc


@app.post("/plan")
async def plan(request: PlanRequest):
    tasks = ResearchPlanner().plan(request.question)
    return {"question": request.question, "tasks": [t.__dict__ for t in tasks]}


@app.post("/orchestrate/update")
async def orchestrate_update(request: OrchestratorUpdate):
    state = orchestrator.start("runtime research state")
    state = orchestrator.update(
        state, evidence_count=request.evidence_count,
        coverage_score=request.coverage_score, disagreements=request.disagreements,
    )
    return {
        "coverage_score": state.coverage_score,
        "evidence_count": state.evidence_count,
        "tasks": [
            {"id": t.id, "role": t.task.role.value, "objective": t.task.objective,
             "status": t.status.value}
            for t in state.tasks.values()
        ],
    }
