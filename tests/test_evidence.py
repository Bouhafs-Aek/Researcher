from researcher.evidence import verify_claim

def test_verification_requires_passage():
    result = verify_claim(
        source_found=True,
        passage_found=False,
        interpretation_checked=True,
        counterevidence_checked=True,
    )
    assert result.status == "unverified"

def test_full_verification():
    result = verify_claim(
        source_found=True,
        passage_found=True,
        interpretation_checked=True,
        counterevidence_checked=True,
    )
    assert result.status == "independently_corroborated"
