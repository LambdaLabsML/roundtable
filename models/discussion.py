from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Optional, Dict, List
from enum import Enum

class Role(Enum):
    MODERATOR = "moderator"
    PANELIST = "panelist"

class Round(Enum):
    AGENDA = 0
    EVIDENCE = 1
    CROSS_EXAMINATION = 2
    CONVERGENCE = 3

@dataclass
class Message:
    participant_id: str
    participant_model: str
    role: Role
    round: Round
    content: str
    timestamp: datetime
    turn_number: int

@dataclass
class CrossExamination:
    strongest_points: Dict[str, str]  # participant_id -> point
    steelman_improvements: Dict[str, str]  # participant_id -> improvement
    concrete_risks: List[str]

@dataclass
class DiscussionState:
    id: str
    topic: str
    current_round: Round
    current_speaker: Optional[str]
    turn_order: List[str]
    transcript: List[Message]
    round_metadata: Dict
    status: Literal["in_progress", "completed", "failed"]
    started_at: datetime
    completed_at: Optional[datetime]
