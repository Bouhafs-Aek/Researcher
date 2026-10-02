from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True)
class GapAssessment:
    classification: str
    rationale: str

def classify_gap(
    *,
    direct_prior_work: bool,
    conflicting_evidence: bool,
    limited_coverage: bool,
    counterevidence_checked: bool,
) -> GapAssessment:
    if direct_prior_work:
        return GapAssessment("previously_addressed", "Relevant prior work was identified.")
    if conflicting_evidence:
        return GapAssessment("conflicting_evidence", "The literature contains materially inconsistent findings.")
    if limited_coverage and counterevidence_checked:
        return GapAssessment("potentially_underexplored", "Search coverage found limited direct evidence after counterevidence checking.")
    return GapAssessment("open_hypothesis", "A candidate gap remains a hypothesis pending stronger evidence.")
