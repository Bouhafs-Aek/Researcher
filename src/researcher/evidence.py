from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True)
class VerificationDecision:
    status: str
    reason: str

ALLOWED_STATUSES = {
    "unverified",
    "source_verified",
    "author_reported",
    "independently_corroborated",
    "contested",
    "superseded",
}

def verify_claim(
    *,
    source_found: bool,
    passage_found: bool,
    interpretation_checked: bool,
    counterevidence_checked: bool,
) -> VerificationDecision:
    if not source_found:
        return VerificationDecision("unverified", "Source identity was not verified.")
    if not passage_found:
        return VerificationDecision("unverified", "No supporting passage was located.")
    if not interpretation_checked:
        return VerificationDecision("source_verified", "Source and passage verified; interpretation not yet audited.")
    if not counterevidence_checked:
        return VerificationDecision("author_reported", "Claim matches the source but counterevidence has not been checked.")
    return VerificationDecision("independently_corroborated", "Source, passage, interpretation, and counterevidence checks completed.")
