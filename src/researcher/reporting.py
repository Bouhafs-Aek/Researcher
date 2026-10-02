from __future__ import annotations

from html import escape

from sqlalchemy.orm import Session

from .repository import Repository


def build_html_report(session: Session, project_id: int) -> str:
    repo = Repository(session)
    project = repo.get_project(project_id)
    if project is None:
        raise ValueError("Project not found")

    sources = repo.list_sources(project_id)
    claims = repo.list_claims(project_id)
    gaps = repo.list_gaps(project_id)

    source_rows = "".join(
        f"<tr><td>{s.id}</td><td>{escape(s.title)}</td><td>{escape(s.doi or '')}</td>"
        f"<td>{s.year or ''}</td><td>{escape(s.provider)}</td></tr>"
        for s in sources
    )
    claim_rows = "".join(
        f"<tr><td>{c.id}</td><td>{escape(c.text)}</td><td>{escape(c.status)}</td></tr>"
        for c in claims
    )
    gap_rows = "".join(
        f"<li><strong>{escape(g.classification)}</strong>: {escape(g.statement)}</li>"
        for g in gaps
    )

    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{escape(project.title)}</title>
<style>
body{{font-family:system-ui,sans-serif;max-width:1100px;margin:40px auto;padding:0 20px}}
table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #ddd;padding:8px;text-align:left}}
section{{margin:32px 0}}
</style></head><body>
<h1>{escape(project.title)}</h1>
<p><strong>Research question:</strong> {escape(project.question)}</p>
<section><h2>Sources ({len(sources)})</h2>
<table><thead><tr><th>ID</th><th>Title</th><th>DOI</th><th>Year</th><th>Provider</th></tr></thead>
<tbody>{source_rows}</tbody></table></section>
<section><h2>Claims ({len(claims)})</h2>
<table><thead><tr><th>ID</th><th>Claim</th><th>Status</th></tr></thead>
<tbody>{claim_rows}</tbody></table></section>
<section><h2>Candidate gaps ({len(gaps)})</h2><ul>{gap_rows}</ul></section>
</body></html>"""
