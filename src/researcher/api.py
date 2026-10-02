from fastapi import FastAPI, HTTPException
from .agents import ResearchPlanner
from .connectors import OpenAlexConnector
from .schemas import SearchRequest
app=FastAPI(title="Researcher",version="0.1.0")
@app.get("/health")
async def health(): return {"status":"ok"}
@app.post("/search")
async def search(request: SearchRequest):
    try:
        records=await OpenAlexConnector().search(request.query,request.max_results)
        return {"count":len(records),"results":[r.model_dump() for r in records]}
    except Exception as exc: raise HTTPException(status_code=502,detail=f"Literature provider error: {exc}") from exc
@app.post("/plan")
async def plan(question: str):
    tasks=ResearchPlanner().plan(question)
    return {"question":question,"tasks":[t.__dict__ for t in tasks]}
