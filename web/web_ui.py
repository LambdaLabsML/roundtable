from typing import TYPE_CHECKING
from models.discussion import Round, Message, Role

if TYPE_CHECKING:
    from web.server import WebSocketManager

class WebUI:
    """Web-based UI that mirrors the terminal UI functionality"""
    
    def __init__(self, websocket_manager: 'WebSocketManager'):
        self.ws_manager = websocket_manager
        self.round_names = {
            Round.AGENDA: "Agenda Framing",
            Round.EVIDENCE: "Evidence Presentation",
            Round.CROSS_EXAMINATION: "Cross-Examination",
            Round.CONVERGENCE: "Convergence"
        }
        
        self.participant_colors = {
            "gpt5": "cyan",
            "claude": "green", 
            "gemini": "yellow",
            "claude_moderator": "magenta"
        }
    
    async def clear_screen(self):
        """Clear the web terminal screen"""
        await self.ws_manager.broadcast({
            'type': 'clear'
        })
    
    async def display_header(self, topic: str, current_round: Round):
        """Display discussion header"""
        await self.ws_manager.broadcast({
            'type': 'header',
            'topic': topic,
            'round': self.round_names[current_round]
        })
    
    async def display_message(self, message: Message):
        """Display a single message"""
        await self.ws_manager.broadcast({
            'type': 'message',
            'participant_id': message.participant_id,
            'participant_model': message.participant_model,
            'content': message.content,
            'is_moderator': message.role == Role.MODERATOR
        })
    
    async def display_thinking(self, participant: str):
        """Show thinking indicator"""
        participant_names = {
            "claude_moderator": "Claude Moderator",
            "claude": "Claude",
            "gpt5": "GPT-5",
            "gemini": "Gemini"
        }
        
        await self.ws_manager.broadcast({
            'type': 'thinking',
            'participant': participant_names.get(participant, participant)
        })
    
    async def display_round_transition(self, from_round: Round, to_round: Round):
        """Display round transition"""
        await self.ws_manager.broadcast({
            'type': 'round_transition',
            'from_round': self.round_names[from_round],
            'to_round': self.round_names[to_round]
        })
    
    async def display_final_consensus(self, consensus: str):
        """Display final consensus"""
        await self.ws_manager.broadcast({
            'type': 'final_consensus',
            'content': consensus
        })
    
    async def send_output(self, content: str, style: str = ''):
        """Send general output message"""
        await self.ws_manager.broadcast({
            'type': 'output',
            'content': content,
            'style': style
        })
    
    async def send_error(self, content: str):
        """Send error message"""
        await self.ws_manager.broadcast({
            'type': 'output',
            'content': content,
            'style': 'error-message'
        })