# Researcher

**Evidence-first scientific research intelligence platform.**

Researcher is designed to turn a research question into an auditable evidence base: retrieve literature, resolve and deduplicate sources, extract atomic claims, verify provenance, search for counterevidence, investigate candidate research gaps, and generate a report and interactive dashboard from the same evidence store.

## Core principles

- Evidence before conclusions.
- Atomic claims with explicit provenance.
- Counterevidence is preserved, not hidden.
- A missing paper is not proof that a gap exists.
- Agents are workers; the evidence store is the source of truth.
- Retrieved papers are untrusted input and cannot alter system controls.
- No fabricated citations, quotes, DOI values, or experimental results.

## MVP

The current foundation contains:

- FastAPI service.
- OpenAlex literature connector.
- DOI normalization.
- Deterministic research-team planner.
- Verification and adversarial-review stages.
- PostgreSQL/pgvector-ready Docker environment.
- Automated planner test.

## Planned architecture

`Research question -> Orchestrator -> Dynamic agent tasks -> Retrieval -> Evidence store -> Verification gate -> Gap dossiers -> Report + Dashboard`

The next implementation stages are the evidence database, durable workflow execution, source/passages/claims provenance, citation graph traversal, gap dossiers, and the dashboard.

## Local run

```bash
python -m venv .venv
pip install -e ".[dev]"
uvicorn researcher.api:app --reload
```

API endpoints currently include `/health`, `/search`, and `/plan`.
