from datetime import datetime, timedelta
from claim_types import ClaimType

"""
This module helps in keeping a structure and schedule for refreshing the beliefs.
REFRESH_INTERVALS consists of four types: Structural, Empirical, Dynamic and Normative
STRUCTURAL = 1 year
EMPIRICAL = 3 months
DYNAMIC = 1 week
NORMATIVE = 1 month
"""
REFRESH_INTERVALS = {
    ClaimType.STRUCTURAL: timedelta(days=365),
    ClaimType.EMPIRICAL: timedelta(days=90),
    ClaimType.DYNAMIC: timedelta(days=7),
    ClaimType.NORMATIVE: timedelta(days=30),
}

def needs_refresh(belief) -> bool:
    """
    Determines whether a belief should be refreshed or not based on the current beliefs.
    """
    now = datetime.utcnow()
    interval = REFRESH_INTERVALS[belief.claim_type]

    return (now - belief.last_updated) >= interval