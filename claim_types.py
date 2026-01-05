from enum import Enum

"""
This module helps in keeping a structure for claim types and decay rates. 
ClaimType consists of four types: Structural, Empirical, Dynamic and Normative
Decay rates are set for each claim type
"""
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

