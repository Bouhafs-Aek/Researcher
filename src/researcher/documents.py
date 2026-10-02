from __future__ import annotations

import hashlib
import io
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx
import fitz


@dataclass
class DownloadedDocument:
    url: str
    content: bytes
    content_type: str
    sha256: str


class DocumentAcquirer:
    """Acquire openly reachable documents without bypassing access controls."""

    def __init__(self, timeout: float = 30.0) -> None:
        self.timeout = timeout

    @staticmethod
    def is_candidate_url(url: str | None) -> bool:
        if not url:
            return False
        path = urlparse(url).path.lower()
        return path.endswith(".pdf") or "arxiv.org/pdf/" in url.lower() or "europepmc.org/articles/" in url.lower()

    async def fetch(self, url: str) -> DownloadedDocument:
        if not self.is_candidate_url(url):
            raise ValueError("URL is not an explicitly supported open-document URL")
        async with httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
            headers={"User-Agent": "Researcher/0.1 (+evidence-first research)"}
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
        content_type = response.headers.get("content-type", "").split(";")[0].lower()
        content = response.content
        if not content.startswith(b"%PDF"):
            raise ValueError("Downloaded resource is not a PDF")
        return DownloadedDocument(
            url=str(response.url),
            content=content,
            content_type=content_type or "application/pdf",
            sha256=hashlib.sha256(content).hexdigest(),
        )


def extract_pdf_pages(content: bytes) -> list[tuple[int, str]]:
    """Extract page-level text with stable page locators."""
    document = fitz.open(stream=io.BytesIO(content), filetype="pdf")
    try:
        return [
            (page_number + 1, page.get_text("text").strip())
            for page_number, page in enumerate(document)
            if page.get_text("text").strip()
        ]
    finally:
        document.close()
