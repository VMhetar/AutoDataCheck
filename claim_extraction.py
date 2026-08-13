"""
Claim extraction module for ADRE.

Bridges Layer 0 (raw reality intake) and Layer 1 (hypothesis injection).

Raw reality enters the system with zero authority. This module converts
untrusted text into structured claims that have not yet survived any
confrontation with reality. Extracted claims are candidates, never truth.

Every extracted claim is wrapped in a BeliefState that starts with low
belief so that downstream machinery (belief_manager, belief_reviewer,
revert_decision) decides what - if anything - deserves elevation.
"""

import asyncio
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from belief_state_schema import BeliefState, Evidence
from claim_types import ClaimType, DECAY_RATES
from llm_call import call_llm

SENTENCE_SPLIT = re.compile(r"(?<=[.!?。！？])\s+")

MIN_CLAIM_LENGTH = 12
MAX_CLAIM_LENGTH = 300

LOW_AUTHORITY_SUPPORT = 0.1
INITIAL_CONFIDENCE = 0.1

CLAIM_TYPE_KEYWORDS = {
    ClaimType.STRUCTURAL: [
        "always", "never", "law of", "is defined as", "invariant",
        "must hold", "by definition", "a priori"
    ],
    ClaimType.EMPIRICAL: [
        "measured", "observed", "experiment", "study", "survey", "shows",
        "data indicates", "evidence suggests", "sample"
    ],
    ClaimType.DYNAMIC: [
        "currently", "as of", "today", "now", "trending", "latest",
        "price", "rate", "breaking"
    ],
    ClaimType.NORMATIVE: [
        "should", "ought", "must", "required", "prohibited", "allowed",
        "standard", "policy", "regulation", "recommended"
    ],
}


@dataclass
class ExtractedClaim:
    claim: str
    source_id: str = "unknown"
    source_type: str = "untrusted"
    claim_type: ClaimType = ClaimType.EMPIRICAL
    support_strength: float = LOW_AUTHORITY_SUPPORT
    timestamp: Optional[datetime] = field(default=None)


def extract_candidate_claims(text: str) -> List[str]:
    """
    Splits raw text into candidate claims.

    Only filters structurally trivial fragments; it does not judge
    truthfulness. Authority is deliberately absent at this stage.
    """
    if not text or not text.strip():
        return []

    raw = SENTENCE_SPLIT.split(text.strip())
    candidates: List[str] = []

    for sentence in raw:
        candidate = sentence.strip().rstrip(";:,")
        if not candidate or len(candidate) < MIN_CLAIM_LENGTH:
            continue
        if len(candidate) > MAX_CLAIM_LENGTH:
            candidate = candidate[:MAX_CLAIM_LENGTH]
        if not _is_candidate(candidate):
            continue
        candidates.append(candidate)

    return candidates


def _is_candidate(candidate: str) -> bool:
    """
    Rejects fragments that cannot carry epistemic content.
    """
    if re.fullmatch(r"[\W\d_]+", candidate):
        return False
    if candidate.count(" ") < 2:
        return False
    return True


def classify_claim(claim_text: str) -> ClaimType:
    """
    Heuristically classifies a claim into a ClaimType.

    Falls back to EMPIRICAL when no keyword family matches.
    """
    lowered = claim_text.lower()

    for claim_type, keywords in CLAIM_TYPE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in lowered:
                return claim_type

    return ClaimType.EMPIRICAL


def build_evidence(
    extracted_claim: ExtractedClaim,
    support_strength: Optional[float] = None,
    timestamp: Optional[datetime] = None,
) -> Evidence:
    """
    Wraps an extracted claim into an Evidence record.

    Incoming reality starts weak: default support strength is low
    and the source type defaults to 'untrusted'.
    """
    return Evidence(
        source_id=extracted_claim.source_id,
        source_type=extracted_claim.source_type,
        support_strength=(
            support_strength
            if support_strength is not None
            else extracted_claim.support_strength
        ),
        timestamp=timestamp or extracted_claim.timestamp or datetime.now(timezone.utc),
    )


def to_belief_state(
    extracted_claim: ExtractedClaim,
    state_id: int = 0,
    now: Optional[datetime] = None,
) -> BeliefState:
    """
    Converts an extracted claim into an unvalidated BeliefState.

    The belief begins at near-zero confidence and zero verification so
    that it must earn its status through evidence and confrontation.
    """
    current_time = now or datetime.now(timezone.utc)

    evidence = build_evidence(extracted_claim)

    return BeliefState(
        state_id=state_id,
        claim=extracted_claim.claim,
        claim_type=extracted_claim.claim_type,
        confidence=INITIAL_CONFIDENCE,
        uncertainty=1.0 - INITIAL_CONFIDENCE,
        evidence=[evidence],
        contradiction_count=0,
        source_diversity=0.0,
        verification_count=0,
        decay_rate=DECAY_RATES[extracted_claim.claim_type],
        last_verified=current_time,
        last_updated=current_time,
        status="speculative",
    )


def extract_claims(
    text: str,
    source_id: str = "unknown",
    source_type: str = "untrusted",
    start_state_id: int = 0,
) -> List[BeliefState]:
    """
    Main pipeline: raw text becomes a list of unvalidated BeliefStates.

    Each sentence that survives the structural filters is classified,
    wrapped in low-authority evidence, and injected as a speculative claim.
    """
    beliefs: List[BeliefState] = []

    for index, candidate in enumerate(extract_candidate_claims(text)):
        extracted = ExtractedClaim(
            claim=candidate,
            source_id=source_id,
            source_type=source_type,
            claim_type=classify_claim(candidate),
        )
        beliefs.append(to_belief_state(extracted, state_id=start_state_id + index))

    return beliefs


async def extract_claims_llm(
    text: str,
    source_id: str = "unknown",
    source_type: str = "untrusted",
    start_state_id: int = 0,
) -> List[BeliefState]:
    """
    LLM-assisted extraction path.

    Uses call_llm to surface claims the heuristic splitter might miss,
    such as implicit hypotheses and counterfactuals. Feeds each one
    through the same low-authority BeliefState injection.
    """
    extraction_prompt = (
        "Extract every standalone claim from the following text. "
        "Return a JSON list of strings. Only return the JSON array, "
        "no prose.\n\nTEXT:\n" + text
    )

    result = None
    try:
        result = await call_llm(extraction_prompt)
    except Exception:
        return extract_claims(text, source_id, source_type, start_state_id)

    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")

    try:
        claims = json.loads(content)
    except (json.JSONDecodeError, TypeError):
        claims = extract_candidate_claims(text)

    if not isinstance(claims, list):
        claims = [claims]

    beliefs: List[BeliefState] = []
    for index, claim in enumerate(claims):
        if not isinstance(claim, str) or not claim.strip():
            continue
        extracted = ExtractedClaim(
            claim=claim.strip(),
            source_id=source_id,
            source_type=source_type,
            claim_type=classify_claim(claim),
        )
        beliefs.append(to_belief_state(extracted, state_id=start_state_id + index))

    if not beliefs:
        return extract_claims(text, source_id, source_type, start_state_id)

    return beliefs


def extract_claims_llm_sync(
    text: str,
    source_id: str = "unknown",
    source_type: str = "untrusted",
    start_state_id: int = 0,
) -> List[BeliefState]:
    """
    Synchronous convenience wrapper around extract_claims_llm.
    """
    return asyncio.run(
        extract_claims_llm(text, source_id, source_type, start_state_id)
    )