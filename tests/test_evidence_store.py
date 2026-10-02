from researcher.evidence_store import EvidenceStore

def test_evidence_link_is_traceable():
    store = EvidenceStore()
    record = store.link("claim-1", "passage-1", confidence=0.8)
    assert record.claim_id == "claim-1"
    assert store.for_claim("claim-1")[0].passage_id == "passage-1"

def test_invalid_confidence_is_rejected():
    store = EvidenceStore()
    try:
        store.link("claim-1", "passage-1", confidence=1.1)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid confidence was accepted")
