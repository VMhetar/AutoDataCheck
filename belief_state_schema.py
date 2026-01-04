from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

"""
Schema definition for representing Evidence containing source_id, dource_type, support_strength and timestamp.
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

"""
Schema defintion for representing BeliefState containing state_id, claim, confidence, uncertainty, evidence, contradiction_count, source_diversity, verification_count, decay_rate, last_verified, last_updated and status.
state_id (int) : Unique identifier for the belief state.   
claim (str) : The claim or proposition being evaluated.
confidence (float) : A numerical value representing the confidence level in the claim (0 to 1).
uncertainty (float) : A numerical value representing the uncertainty level in the claim (0 to 1).
evidence (List[Evidence]) : A list of Evidence objects supporting or contradicting the claim.
contradiction_count (int) : The number of pieces of evidence that contradict the claim.
source_diversity (float) : A numerical value representing the diversity of sources providing evidence for the claim.
verification_count (int) : The number of times the claim has been verified.
decay_rate (float) : A numerical value representing the rate at which the confidence level decays over time.
last_verified (datetime) : The date and time when the claim was last verified.
last_updated (datetime) : The date and time when the belief state was last updated.
status (str) : The current status of the belief state (e.g., 'unverified', 'verified', 'contradicted').
"""
@dataclass
class BeliefState:
    state_id: int
    claim: str

    confidence: float         
    uncertainty: float      

    evidence: List[Evidence]
    contradiction_count: int

    source_diversity: float
    verification_count: int

    decay_rate: float
    last_verified: datetime
    last_updated: datetime

    status: str            
