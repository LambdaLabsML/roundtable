import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from models.discussion import DiscussionState, Message, Round, Role

class SessionLogger:
    def __init__(self, sessions_dir: str = "sessions"):
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(exist_ok=True)
    
    def save_session(self, state: DiscussionState) -> str:
        """Save discussion state to disk"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_topic = "".join(c for c in state.topic if c.isalnum() or c in (' ', '-', '_'))[:50]
        filename = f"{timestamp}_{safe_topic}.json"
        filepath = self.sessions_dir / filename
        
        # Convert to serializable format
        session_data = {
            "id": state.id,
            "topic": state.topic,
            "status": state.status,
            "started_at": state.started_at.isoformat(),
            "completed_at": state.completed_at.isoformat() if state.completed_at else None,
            "transcript": [
                {
                    "participant_id": msg.participant_id,
                    "participant_model": msg.participant_model,
                    "role": msg.role.value,
                    "round": msg.round.value,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "turn_number": msg.turn_number
                }
                for msg in state.transcript
            ],
            "round_metadata": state.round_metadata
        }
        
        with open(filepath, 'w') as f:
            json.dump(session_data, f, indent=2)
        
        return str(filepath)
    
    def load_session(self, filename: str) -> Optional[DiscussionState]:
        """Load discussion state from disk"""
        filepath = self.sessions_dir / filename
        
        if not filepath.exists():
            return None
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Reconstruct state
        transcript = [
            Message(
                participant_id=msg["participant_id"],
                participant_model=msg["participant_model"],
                role=Role(msg["role"]),
                round=Round(msg["round"]),
                content=msg["content"],
                timestamp=datetime.fromisoformat(msg["timestamp"]),
                turn_number=msg["turn_number"]
            )
            for msg in data["transcript"]
        ]
        
        state = DiscussionState(
            id=data["id"],
            topic=data["topic"],
            current_round=Round(len(data["round_metadata"]) - 1) if data["round_metadata"] else Round.AGENDA,
            current_speaker=None,
            turn_order=[],
            transcript=transcript,
            round_metadata=data["round_metadata"],
            status=data["status"],
            started_at=datetime.fromisoformat(data["started_at"]),
            completed_at=datetime.fromisoformat(data["completed_at"]) if data["completed_at"] else None
        )
        
        return state
    
    def list_sessions(self) -> List[tuple[str, str, str]]:
        """List all saved sessions"""
        sessions = []
        for filepath in sorted(self.sessions_dir.glob("*.json"), reverse=True):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    sessions.append((
                        filepath.name,
                        data["topic"],
                        data["started_at"]
                    ))
            except:
                continue
        return sessions
    
    def autosave(self, state: DiscussionState, filename: Optional[str] = None):
        """Autosave current state (overwrites if filename provided)"""
        if filename:
            filepath = self.sessions_dir / filename
        else:
            # Create autosave file
            filepath = self.sessions_dir / f"autosave_{state.id}.json"
        
        session_data = {
            "id": state.id,
            "topic": state.topic,
            "current_round": state.current_round.value,
            "status": state.status,
            "started_at": state.started_at.isoformat(),
            "transcript": [
                {
                    "participant_id": msg.participant_id,
                    "participant_model": msg.participant_model,
                    "role": msg.role.value,
                    "round": msg.round.value,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "turn_number": msg.turn_number
                }
                for msg in state.transcript
            ],
            "round_metadata": state.round_metadata
        }
        
        with open(filepath, 'w') as f:
            json.dump(session_data, f, indent=2)
