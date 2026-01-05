from belief_math import compute_confidence
from claim_types import DECAY_RATES

def update_belief_confidence(belief):
    decay_rate = DECAY_RATES[belief.claim_type]

    belief.confidence = compute_confidence(
        evidence_list=belief.evidence,
        last_verified=belief.last_verified,
        decay_rate=decay_rate
    )

def update_belief_status(belief):
    belief.status = update_belief_confidence(belief)