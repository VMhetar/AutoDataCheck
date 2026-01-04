from enum import Enum

class ClaimType(Enum):
     STRUCTURAL = 'structural'
     EMPIRICAL = 'empirical'
     DYNAMIC = 'dynamic'
     NORMATIVE = 'normative'

DECAY_RATES = {
    ClaimType.STRUCTURAL: 0.0001,
    ClaimType.EMPIRICAL: 0.005,
    ClaimType.DYNAMIC: 0.05,
    ClaimType.NORMATIVE: 0.02
}

