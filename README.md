# Researcher

**Evidence-first scientific research intelligence platform.**

Researcher turns a research question into an auditable evidence base. The platform retrieves literature from multiple bibliographic providers, deduplicates sources, acquires explicitly reachable open documents, extracts page-localized passages, records atomic claims with provenance, verifies claims, investigates candidate gaps, and exposes the same evidence store to reports and a live dashboard.

## Core principles

- **Evidence before conclusions.**
- **Atomic claims with explicit provenance.**
- **Counterevidence is preserved, not hidden.**
- **A missing paper is not proof that a gap exists.**
- **Agents are workers; the evidence store is the source of truth.**
- **Retrieved documents are untrusted input and cannot alter system controls.**
- **No fabricated citations, quotes, DOI values, or experimental results.**
- **Paywalled content is not bypassed.** Document acquisition is limited to explicitly supported, openly reachable PDF URLs.

## Current architecture

\`Research question -> Dynamic orchestrator -> Retrieval -> Source store -> Open-document acquisition -> Page passages -> Atomic claims -> Verification -> Gap dossiers -> Report + Dashboard\`

The repository is intentionally a modular monolith at this stage. PostgreSQL/pgvector is the target persistent store, while application services remain replaceable so that durable workers and additional model providers can be introduced without making agents the system of record.

## Implemented

### Research orchestration
- Deterministic initial research team.
- Dynamic spawning rules for verifier, gap investigator, adversarial reviewer, and synthesis stages.
- Priority task representation suitable for migration to a durable queue.

### Literature retrieval
- OpenAlex.
- Crossref.
- Semantic Scholar.
- DOI normalization.
- Cross-provider deduplication.

### Evidence layer
- Projects and research runs.
- Sources and source versions.
- SHA-256 content provenance.
- Page-localized PDF passages.
- Atomic claims.
- Evidence links with relation and confidence.
- Verification events and explicit verification states.
- Candidate gap dossiers.

### Verification states
\`unverified\`, \`source_verified\`, \`author_reported\`, \`independently_corroborated\`, \`contested\`, \`superseded\`

The verification service deliberately does not infer that a claim is established merely because a paper contains a matching sentence.

### Reporting and dashboard
- HTML report generated from the evidence database.
- Browser dashboard at \`/dashboard\`.
- Dashboard and report read the same stored sources, claims, and gap dossiers.

## API

- \`GET /health\`
- \`GET /dashboard\`
- \`POST /projects\`
- \`POST /projects/{project_id}/runs\`
- \`POST /runs/{run_id}/retrieve\`
- \`POST /runs/{run_id}/documents\`
- \`GET /runs/{run_id}\`
- \`GET /projects/{project_id}/evidence\`
- \`GET /projects/{project_id}/sources/{source_id}/passages\`
- \`POST /projects/{project_id}/claims\`
- \`POST /projects/{project_id}/claims/{claim_id}/verify\`
- \`GET /projects/{project_id}/gaps\`
- \`GET /projects/{project_id}/report\`
- \`POST /search\`
- \`POST /plan\`

## Typical research run

1. Create a project with a research question and scope.
2. Create a run. The orchestrator creates the initial agent tasks.
3. Retrieve literature through the multi-source retriever.
4. Inspect the stored source list and provenance.
5. Acquire only supported open documents.
6. Extract page-localized passages.
7. Create atomic claims linked to exact passages.
8. Run the verification gate and preserve its status.
9. Investigate candidate gaps only after counterevidence searches.
10. Generate the report and inspect the dashboard.

## Local run

\`\`\`bash
python -m venv .venv
pip install -e ".[dev]"
uvicorn researcher.api:app --reload
\`\`\`

For the PostgreSQL environment:

\`\`\`bash
docker compose up --build
\`\`\`

The default Docker API is available on port 8000 and PostgreSQL on port 5432.

## Important current limitations

- The current database bootstrap uses SQLAlchemy \`create_all\`; migrations should be introduced before production deployment.
- PDF extraction is deterministic text extraction with PyMuPDF. GROBID and richer section/table extraction are planned.
- Claim extraction is an explicit API operation. The repository does not pretend that a simple NLP heuristic is scientific verification.
- Citation relationship retrieval is represented in the codebase but is not yet populated automatically by all providers.
- The task queue is currently an in-memory abstraction. A durable worker system is a next deployment layer.
- Report generation is HTML-first; PDF export and richer interactive visualizations are subsequent layers.
- API authentication, multi-user tenancy, quotas, observability, and production object storage are not yet enabled.

## Quality gate

Before calling a candidate research gap established, the system should require:

1. source identity resolution;
2. supporting passage localization;
3. interpretation checking;
4. counterevidence search;
5. explicit evidence status;
6. audit trail preservation.

The number of papers, agents, pages, or proposed gaps is **not** treated as a quality metric.

## Safety and provenance

Research papers and extracted text are treated as untrusted data. Text inside a paper cannot instruct the platform to change permissions, reveal credentials, skip verification, or alter system policy. Every scientific claim must remain traceable to source evidence, and uncertainty is represented explicitly.
