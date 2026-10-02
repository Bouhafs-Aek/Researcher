from __future__ import annotations

import httpx

from .config import settings
from .schemas import SourceRecord


class OpenAlexConnector:
    endpoint = "https://api.openalex.org/works"

    async def search(self, query: str, max_results: int = 20) -> list[SourceRecord]:
        params = {"search": query, "per-page": max_results}
        if settings.openalex_mailto:
            params["mailto"] = settings.openalex_mailto
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(self.endpoint, params=params)
            response.raise_for_status()
            data = response.json()

        records: list[SourceRecord] = []
        for item in data.get("results", []):
            primary = item.get("primary_location") or {}
            best_oa = item.get("best_oa_location") or {}
            url = (
                best_oa.get("pdf_url")
                or primary.get("pdf_url")
                or primary.get("landing_page_url")
                or item.get("doi")
            )
            records.append(
                SourceRecord(
                    title=item.get("display_name") or "Untitled",
                    doi=_normalize_doi(item.get("doi")),
                    year=item.get("publication_year"),
                    venue=((primary.get("source") or {}).get("display_name")),
                    url=url,
                    source="openalex",
                )
            )
        return records


def _normalize_doi(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if value.lower().startswith(prefix):
            value = value[len(prefix):]
            break
    return value.lower().rstrip(" .")
