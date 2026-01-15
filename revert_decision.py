from datetime import datetime, timedelta
from claim_types import ClaimType

def should_revert(belief) -> dict:
    """
    Determines whether a belief decision should be reverted.
    Returns a recommendation, not an action.
    """

    decision = {
        "revert": False,
        "target_status": None,
        "reason": []
    }

    if not belief.history or len(belief.history) < 2:
        return decision

    last_state = belief.history[-1]
    prev_state = belief.history[-2]

    if belief.confidence > prev_state["confidence"] + 0.2:
        decision["revert"] = True
        decision["target_status"] = prev_state["status"]
        decision["reason"].append("confidence recovered significantly")

    if belief.claim_type == ClaimType.DYNAMIC:
        if belief.confidence > 0.5 and prev_state["status"] == "rejected":
            decision["revert"] = True
            decision["target_status"] = "speculative"
            decision["reason"].append("dynamic claim recovery")

    if "decay" in last_state.get("reason", "").lower():
        decision["revert"] = True
        decision["target_status"] = prev_state["status"]
        decision["reason"].append("rejection due to decay, not contradiction")

    return decision