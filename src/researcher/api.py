from fastapi import FastAPI, HTTPException
from .agents import ResearchPlanner
from .connectors import OpenAlexConnector
from .config import settings
from .db import init_db
from .orchestrator import DynamicOrchestrator
from .schemas import OrchestratorUpdate, PlanRequest, SearchRequest

app = FastAPI(title="Researcher", version="0.1.0")
orchestrator = DynamicOrchestrator()

@app.on_event("startup")
def startup() -> None:
    if settings.app_env != "test":
        init_db()

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

@app.post("/search")
async def search(request: SearchRequest):
    try:
        records = await OpenAlexConnector().search(request.query, request.max_results)
        return {"count": len(records), "results": [r.model_dump() for r in records]}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Literature provider error: {exc}") from exc

@app.post("/plan")
async def plan(request: PlanRequest):
    tasks = ResearchPlanner().plan(request.question)
    return {"question": request.question, "tasks": [t.__dict__ for t in tasks]}

@app.post("/orchestrate/start")
async def orchestrate_start(request: PlanRequest):
    state = orchestrator.start(request.question)
    return {
        "question": state.question,
        "tasks": [
            {"id": t.id, "role": t.task.role.value, "objective": t.task.objective,
             "status": t.status.value}
            for t in state.tasks.values()
        ],
    }

@app.post("/orchestrate/update")
async def orchestrate_update(request: OrchestratorUpdate):
    state = orchestrator.start("runtime research state")
    state = orchestrator.update(
        state,
        evidence_count=request.evidence_count,
        coverage_score=request.coverage_score,
        disagreements=request.disagreements,
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
