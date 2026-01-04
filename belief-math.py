"""
Docstring for belief-math
This module provides the fundamental mathematics for everything related to belief states and evidence handling of belief_state_schema.py
It includes functions for updating belief states based on new evidence, calculating confidence and uncertainty levels,and managing the decay of belief over time.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Set
import math

"""
Data structure for representing Evidence containing source_id, source_type, support_strength and timestamp.
source_id (str) : Unique identifier for the source providing the evidence.
source_type (str) : Type of the source (e.g., 'news', 'social_media', 'official_report').
support_strength (float) : A numerical value representing the strength of support the evidence provides to the claim.
timestamp (datetime) : The date and time when the evidence was recorded.
"""
@dataclass
class Evidence:
    source_id:str
    source_type:str
    support_strength:float
    timestamp: datetime

def evidence_support(evidence_list: List[Evidence]) -> float:
    """
    This module calculates the support strength of a list of evidence and penalizes contradictory evidence.
    It returns a float value representing the overall support strength.
    """
    contradictions = sum(1 for e in evidence_list if e.support_strength < 0 )
    penalty = contradictions * 0.1
    return min(0.5, penalty)

