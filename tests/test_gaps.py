from researcher.gaps import classify_gap

def test_gap_is_not_established_without_counterevidence_check():
    result = classify_gap(
        direct_prior_work=False,
        conflicting_evidence=False,
        limited_coverage=True,
        counterevidence_checked=False,
    )
    assert result.classification == "open_hypothesis"

def test_underexplored_requires_counterevidence_check():
    result = classify_gap(
        direct_prior_work=False,
        conflicting_evidence=False,
        limited_coverage=True,
        counterevidence_checked=True,
    )
    assert result.classification == "potentially_underexplored"
