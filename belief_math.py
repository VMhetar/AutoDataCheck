"""
This module contains the core epistemic computation functions.
Every function in this module flows through this file.

Epistemic computation utilities for ADRE.
All belief confidence must flow through this file.

"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Set
import math


"""
The below dataclass represents Evidence containing source_id, dource_type, support_strength and timestamp.
source_id (str) : Unique identifier for the source providing the evidence.
source_type (str) : Type of the source (e.g., 'news', 'social_media', 'official_report').
support_strength (float) : A numerical value representing the strength of support the evidence provides to the claim.
timestamp (datetime) : The date and time when the evidence was recorded.
"""
@dataclass
class Evidence:
    source_id: str       
    source_type: str       
    support_strength: float    
    timestamp: datetime

def evidence_support(evidence_list: List[Evidence]) -> float:
    """
    Computes mean support strength of all evidence.
    """
    if not evidence_list:
        return 0.0

    return sum(e.support_strength for e in evidence_list) / len(evidence_list)


def contradiction_penalty(evidence_list: List[Evidence]) -> float:
    """
    Penalizes confidence based on contradicting evidence.
    Contradictions hurt more than confirmations help.
    """
    contradictions = sum(1 for e in evidence_list if e.support_strength < 0)

    penalty = contradictions * 0.1
    return min(0.5, penalty)


def source_diversity_bonus(evidence_list: List[Evidence]) -> float:
    """
    Rewards independent confirmation across diverse sources.
    Source diversity helps prevent confirmation bias.
    """
    if not evidence_list:
        return 0.0

    unique_sources: Set[str] = {e.source_id for e in evidence_list}
    diversity_ratio = len(unique_sources) / len(evidence_list)

    return min(0.3, diversity_ratio)


def time_decay(last_verified: datetime, decay_rate: float = 0.01) -> float:
    """
    Truth expires unless refreshed.
    Uses exponential decay.
    Useful for preventing the issues of bias over time
    """
    days_passed = (datetime.utcnow() - last_verified).days

    if days_passed <= 0:
        return 0.0

    return 1 - math.exp(-decay_rate * days_passed)


def uncertainty_score(confidence: float) -> float:
    """
    Explicit uncertainty representation.
    Not just (1 - confidence), but clipped for safety.
    """
    return max(0.0, min(1.0, 1.0 - confidence))

def compute_confidence(
    evidence_list: List[Evidence],
    last_verified: datetime,
    base_confidence: float = 0.5,
    decay_rate: float = 0.01
) -> float:
    """
    Computes epistemic confidence for a belief.
    """

    support = evidence_support(evidence_list)
    contradiction = contradiction_penalty(evidence_list)
    diversity = source_diversity_bonus(evidence_list)
    decay = time_decay(last_verified, decay_rate)

    confidence = (
        base_confidence
        + support
        + diversity
        - contradiction
        - decay
    )

    return max(0.0, min(1.0, confidence))


def belief_status(confidence: float) -> str:
    """
    Maps confidence to belief status.
    """

    if confidence < 0.3:
        return "rejected"
    elif confidence < 0.5:
        return "speculative"
    elif confidence < 0.75:
        return "contextual"
    else:
        return "stable"
