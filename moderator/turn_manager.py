from typing import List, Optional
from models.discussion import DiscussionState, Round
import random

class TurnManager:
    def __init__(self):
        self.panelist_ids = ["gpt5", "claude", "gemini", "deepseek"]
        self.moderator_id = "claude_moderator"
    
    def determine_next_speaker(self, state: DiscussionState) -> str:
        """Determine who speaks next based on round and state"""
        
        if state.current_round == Round.AGENDA:
            return self.moderator_id
        
        elif state.current_round == Round.EVIDENCE:
            spoken = {msg.participant_id for msg in state.transcript 
                     if msg.round == Round.EVIDENCE}
            remaining = [p for p in self.panelist_ids if p not in spoken]
            
            if not remaining:
                return self.moderator_id
            
            return random.choice(remaining)
        
        elif state.current_round == Round.CROSS_EXAMINATION:
            examined = {msg.participant_id for msg in state.transcript 
                       if msg.round == Round.CROSS_EXAMINATION}
            remaining = [p for p in self.panelist_ids if p not in examined]
            
            if not remaining:
                return self.moderator_id
            
            return remaining[0]
        
        elif state.current_round == Round.CONVERGENCE:
            messages_in_round = [msg for msg in state.transcript 
                                if msg.round == Round.CONVERGENCE]
            
            if len(messages_in_round) == 0:
                return self.moderator_id
            elif len(messages_in_round) <= len(self.panelist_ids):
                responded = {msg.participant_id for msg in messages_in_round[1:]}
                remaining = [p for p in self.panelist_ids if p not in responded]
                if remaining:
                    return remaining[0]
            
            return self.moderator_id
    
    def should_advance_round(self, state: DiscussionState) -> bool:
        """Check if current round is complete"""
        if state.current_round == Round.AGENDA:
            return any(msg.participant_id == self.moderator_id 
                      for msg in state.transcript)
        
        elif state.current_round == Round.EVIDENCE:
            spoken = {msg.participant_id for msg in state.transcript 
                     if msg.round == Round.EVIDENCE}
            return len(spoken) == len(self.panelist_ids)
        
        elif state.current_round == Round.CROSS_EXAMINATION:
            examined = {msg.participant_id for msg in state.transcript 
                       if msg.round == Round.CROSS_EXAMINATION}
            return len(examined) == len(self.panelist_ids)
        
        elif state.current_round == Round.CONVERGENCE:
            messages_in_round = [msg for msg in state.transcript 
                                if msg.round == Round.CONVERGENCE]
            return len(messages_in_round) >= len(self.panelist_ids) + 2
        
        return False
