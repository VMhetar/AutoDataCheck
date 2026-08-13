from belief_math import compute_confidence, belief_status
from claim_types import DECAY_RATES
from datetime import datetime, timezone


def update_belief_confidence(belief):
    """
    Recomputes and updates belief confidence based on evidence and decay.
    """
    decay_rate = DECAY_RATES[belief.claim_type]

    belief.confidence = compute_confidence(
        evidence_list=belief.evidence,
        last_verified=belief.last_verified,
        decay_rate=decay_rate
    )

    return belief.confidence


def update_belief_status(belief):
    """
    Updates belief status based on current confidence.
    """
    belief.status = belief_status(belief.confidence)
    return belief.status


def refresh_belief(belief):
    """
    Performs a full belief refresh cycle.
    """
    now = datetime.now(timezone.utc)

    decay_rate = DECAY_RATES[belief.claim_type]

    belief.confidence = compute_confidence(
        evidence_list=belief.evidence,
        last_verified=belief.last_verified,
        decay_rate=decay_rate
    )

    belief.status = belief_status(belief.confidence)
    belief.last_updated = now

    belief.verification_count += 1

    belief.history.append({
        "confidence": belief.confidence,
        "status": belief.status,
        "timestamp": now.isoformat(),
        "reason": "refresh cycle"
    })

    return belief