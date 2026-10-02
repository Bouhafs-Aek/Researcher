import pytest

from researcher.documents import DocumentAcquirer, extract_pdf_pages


def test_pdf_url_filter():
    assert DocumentAcquirer.is_candidate_url("https://example.org/paper.pdf")
    assert not DocumentAcquirer.is_candidate_url("https://example.org/article")


def test_pdf_extraction():
    fitz = pytest.importorskip("fitz")
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "Evidence passage.")
    data = document.tobytes()
    document.close()
    pages = extract_pdf_pages(data)
    assert pages == [(1, "Evidence passage.")]
