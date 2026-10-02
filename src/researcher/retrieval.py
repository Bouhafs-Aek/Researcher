from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote

import httpx

from .schemas import SourceRecord


@dataclass(frozen=True)
class SearchHit:
    record: SourceRecord
    provider: str
    query: str


class CrossrefConnector:
    endpoint = "https://api.crossref.org/works"

    async def search(self, query: str, max_results: int = 20) -> list[SourceRecord]:
        params = {"query.bibliographic": query, "rows": max_results}
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(self.endpoint, params=params)
            response.raise_for_status()
            items = response.json()["message"]["items"]

        records: list[SourceRecord] = []
        for item in items:
            doi = item.get("DOI")
            title = (item.get("title") or ["Untitled"])[0]
            year = None
            dates = item.get("published-print") or item.get("published-online")
            if dates and dates.get("date-parts"):
                year = dates["date-parts"][0][0]
            records.append(SourceRecord(
                title=title,
                doi=doi.lower() if doi else None,
                year=year,
                venue=(item.get("container-title") or [None])[0],
                url=f"https://doi.org/{quote(doi)}" if doi else None,
                source="crossref",
            ))
        return records


class SemanticScholarConnector:
    endpoint = "https://api.semanticscholar.org/graph/v1/paper/search"

    async def search(self, query: str, max_results: int = 20) -> list[SourceRecord]:
        params = {
            "query": query,
            "limit": max_results,
            "fields": "title,year,venue,externalIds,url",
        }
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(self.endpoint, params=params)
            response.raise_for_status()
            items = response.json().get("data", [])

        records: list[SourceRecord] = []
        for item in items:
            ids = item.get("externalIds") or {}
            doi = ids.get("DOI")
            records.append(SourceRecord(
                title=item.get("title") or "Untitled",
                doi=doi.lower() if doi else None,
                year=item.get("year"),
                venue=item.get("venue"),
                url=item.get("url"),
                source="semantic_scholar",
            ))
        return records


class MultiSourceRetriever:
    def __init__(self) -> None:
        self.providers = (
            OpenAlexConnector(),
            CrossrefConnector(),
            SemanticScholarConnector(),
        )

    async def search(self, query: str, max_results: int = 20) -> list[SourceRecord]:
        results: list[SourceRecord] = []
        per_provider = max(1, max_results // len(self.providers))

        async with httpx.AsyncClient(timeout=20):
            for provider in self.providers:
                try:
                    results.extend(await provider.search(query, per_provider))
                except httpx.HTTPError:
                    continue

        return deduplicate_sources(results)


def deduplicate_sources(records: list[SourceRecord]) -> list[SourceRecord]:
    """Prefer DOI identity, then normalized title/year identity."""
    seen: set[str] = set()
    unique: list[SourceRecord] = []

    for record in records:
        title_key = " ".join(record.title.lower().split())
        key = f"doi:{record.doi}" if record.doi else f"title:{title_key}|year:{record.year}"
        if key in seen:
            continue
        seen.add(key)
        unique.append(record)

    return unique
