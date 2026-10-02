from fastapi import FastAPI, HTTPException
from sqlalchemy.orm import Session

from .agents import ResearchPlanner
from .config import settings
from .db import SessionLocal, init_db
from .orchestrator import DynamicOrchestrator
from .repository import Repository
from .retrieval import MultiSourceRetriever
from .schemas import OrchestratorUpdate, PlanRequest, ResearchProjectCreate, SearchRequest

app = FastAPI(title="Researcher", version="0.1.0")
orchestrator = DynamicOrchestrator()
retriever = MultiSourceRetriever()

@app.on_event("startup")
def startup() -> None:
    if settings.app_env != "test":
        init_db()

def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

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
        tasks = orchestrator.start(project.question)
        for item in tasks.tasks.values():
            repo.add_task(run.id, item.task.role.value, item.task.objective)
        session.commit()
        return {
            "run_id": run.id,
            "project_id": project_id,
            "status": run.status,
            "tasks": repo.list_tasks(run.id),
        }
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
            "id": run.id,
            "project_id": run.project_id,
            "status": run.status,
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
            "sources": [s.__dict__ | {"_sa_instance_state": None} for s in repo.list_sources(project_id)],
            "claims": [c.__dict__ | {"_sa_instance_state": None} for c in repo.list_claims(project_id)],
        }
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
    state = orchestrator.update(state, evidence_count=request.evidence_count,
                                coverage_score=request.coverage_score,
                                disagreements=request.disagreements)
    return {
        "coverage_score": state.coverage_score,
        "evidence_count": state.evidence_count,
        "tasks": [
            {"id": t.id, "role": t.task.role.value, "objective": t.task.objective,
             "status": t.status.value}
            for t in state.tasks.values()
        ],
    }
