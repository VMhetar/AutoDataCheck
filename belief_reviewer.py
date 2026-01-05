from datetime import datetime, timedelta,timezone
from claim_types import ClaimType

def review_belief(belief) -> dict:
    """
    Reviews a belief and returns a recommended action.
    Does not mutate belief state.
    """

    recommendations = {
        "refresh":False,
        "reverify":False,
        "downgrade":False,
        "reason":[]
    }

    now = datetime.now(timezone.utc)

    if belief.confidence < 0.3:
        recommendations["downgrade"] = True
        recommendations['reason'].append('Confidence too low.')
    
    if belief.claim_type == ClaimType.DYNAMIC:
        if (now - belief.last_verified) > timedelta(days=7):
            recommendations["reverify"] = True
            recommendations["reason"].append("dynamic claim is stale")
    
    if belief.contradiction_count >= 3:
        recommendations["reverify"] = True
        recommendations["reason"].append("too many contradictions")

    if (now - belief.last_updated) > timedelta(days=30):
        recommendations["refresh"] = True
        recommendations["reason"].append("belief not refreshed recently")

    return recommendations