import asyncio
import json
import logging
import os
import signal
import sys
import traceback
import uuid
import websockets
from datetime import datetime
from pathlib import Path
from typing import Set, Optional
from websockets.server import WebSocketServerProtocol

# Add parent directory to path to import roundtable modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.discussion import DiscussionState, Round, Message, Role
from llm.anthropic_client import ClaudeClient
from llm.openai_client import GPTClient
from llm.google_client import GeminiClient
from moderator.turn_manager import TurnManager
from storage.session_logger import SessionLogger
from config import API_KEYS
from web.web_ui import WebUI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self):
        self.clients: Set[WebSocketServerProtocol] = set()
        self.current_session: Optional['WebRoundtableSession'] = None
        
    async def register_client(self, websocket: WebSocketServerProtocol):
        """Register a new WebSocket client"""
        self.clients.add(websocket)
        logger.info(f"Client {websocket.remote_address} connected")
        
        # Send welcome menu to new client
        await self.send_to_client(websocket, {
            'type': 'menu'
        })
    
    async def unregister_client(self, websocket: WebSocketServerProtocol):
        """Unregister a WebSocket client"""
        self.clients.discard(websocket)
        logger.info(f"Client {websocket.remote_address} disconnected")
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        if not self.clients:
            return
            
        await asyncio.gather(
            *[self.send_to_client(client, message) for client in self.clients],
            return_exceptions=True
        )
    
    async def send_to_client(self, websocket: WebSocketServerProtocol, message: dict):
        """Send message to specific client"""
        try:
            await websocket.send(json.dumps(message))
        except websockets.exceptions.ConnectionClosed:
            self.clients.discard(websocket)
        except Exception as e:
            logger.error(f"Error sending message to client: {e}")

class WebRoundtableSession:
    def __init__(self, websocket_manager: WebSocketManager):
        self.ws_manager = websocket_manager
        self.ui = WebUI(websocket_manager)
        self.logger = SessionLogger()
        self.turn_manager = TurnManager()
        
        # Check API keys
        self.check_api_keys()
        
        # Initialize LLM clients
        try:
            self.clients = {
                "claude_moderator": ClaudeClient(API_KEYS["anthropic"]),
                "claude": ClaudeClient(API_KEYS["anthropic"]),
                "gpt5": GPTClient(API_KEYS["openai"]),
                "gemini": GeminiClient(API_KEYS["google"])
            }
        except Exception as e:
            asyncio.create_task(self.ui.send_error(f"Error initializing LLM clients: {e}"))
            asyncio.create_task(self.ui.send_output("Please check your API keys in .env file"))
            raise
        
        self.participant_models = {
            "claude_moderator": "Claude 4.1 Opus",
            "claude": "Claude 4.1 Opus", 
            "gpt5": "GPT-5 Thinking",
            "gemini": "Gemini 2.5 Pro"
        }
        
        self.current_state = None
    
    def check_api_keys(self):
        """Check if API keys are set"""
        missing_keys = []
        for service, key in API_KEYS.items():
            if not key or key == f"your_{service}_api_key_here":
                missing_keys.append(service.upper())
        
        if missing_keys:
            raise Exception(f"Missing API keys: {', '.join(missing_keys)}")
    
    def load_prompts(self) -> tuple[str, str]:
        """Load prompt templates"""
        try:
            with open('prompts/moderator.txt', 'r') as f:
                moderator_prompt = f.read()
            with open('prompts/panelist.txt', 'r') as f:
                panelist_prompt = f.read()
            return moderator_prompt, panelist_prompt
        except FileNotFoundError as e:
            raise Exception(f"Error loading prompts: {e}")
    
    async def generate_response(
        self,
        participant_id: str,
        state: DiscussionState,
        is_moderator: bool = False
    ) -> str:
        """Generate response from LLM"""
        moderator_prompt, panelist_prompt = self.load_prompts()
        
        # Prepare conversation history
        history = []
        for msg in state.transcript:
            history.append({
                "role": "assistant" if msg.participant_id == participant_id else "user",
                "content": f"[{msg.participant_model}]: {msg.content}"
            })
        
        # If this is the first message, add default user message
        if not history:
            history.append({
                "role": "user",
                "content": f"Let's begin the discussion on: {state.topic}"
            })
        
        # Select appropriate prompt
        round_names = {
            Round.AGENDA: "Agenda Framing",
            Round.EVIDENCE: "Evidence Presentation", 
            Round.CROSS_EXAMINATION: "Cross-Examination",
            Round.CONVERGENCE: "Convergence"
        }
        
        if is_moderator:
            system_prompt = moderator_prompt.format(
                round=state.current_round.value,
                round_name=round_names[state.current_round]
            )
        else:
            system_prompt = panelist_prompt.format(
                round=state.current_round.value,
                round_name=round_names[state.current_round]
            )
        
        # Generate response
        client = self.clients[participant_id]
        
        try:
            response = await client.generate_response(
                system_prompt=system_prompt,
                messages=history,
                temperature=0.7
            )
            return response
        except Exception as e:
            await self.ui.send_error(f"Error from {participant_id}: {str(e)}")
            raise
    
    async def run_discussion(self, topic: str):
        """Run a full discussion"""
        # Initialize state
        self.current_state = DiscussionState(
            id=str(uuid.uuid4()),
            topic=topic,
            current_round=Round.AGENDA,
            current_speaker=None,
            turn_order=[],
            transcript=[],
            round_metadata={},
            status="in_progress",
            started_at=datetime.now(),
            completed_at=None
        )
        
        turn_number = 0
        retry_count = 0
        max_retries = 3
        
        while self.current_state.status == "in_progress":
            # Display current state
            await self.ui.clear_screen()
            await self.ui.display_header(topic, self.current_state.current_round)
            
            # Show recent messages (last 3)
            for msg in self.current_state.transcript[-3:]:
                await self.ui.display_message(msg)
            
            # Determine next speaker
            next_speaker = self.turn_manager.determine_next_speaker(self.current_state)
            self.current_state.current_speaker = next_speaker
            
            # Show thinking indicator
            await self.ui.display_thinking(next_speaker)
            
            is_moderator = next_speaker == "claude_moderator"
            
            try:
                response = await self.generate_response(
                    next_speaker,
                    self.current_state,
                    is_moderator
                )
                retry_count = 0  # Reset on success
            except Exception as e:
                retry_count += 1
                await self.ui.send_error(f"Error generating response (attempt {retry_count}/{max_retries}): {e}")
                
                if retry_count >= max_retries:
                    await self.ui.send_error("Max retries exceeded. Exiting.")
                    return
                
                await self.ui.send_output("Retrying in 3 seconds...")
                await asyncio.sleep(3)
                continue
            
            # Add to transcript
            message = Message(
                participant_id=next_speaker,
                participant_model=self.participant_models[next_speaker],
                role=Role.MODERATOR if is_moderator else Role.PANELIST,
                round=self.current_state.current_round,
                content=response,
                timestamp=datetime.now(),
                turn_number=turn_number
            )
            
            self.current_state.transcript.append(message)
            turn_number += 1
            
            # Check for round advancement
            if self.turn_manager.should_advance_round(self.current_state):
                if self.current_state.current_round == Round.CONVERGENCE:
                    # Discussion complete
                    self.current_state.status = "completed"
                    self.current_state.completed_at = datetime.now()
                    
                    # Extract final consensus
                    final_message = self.current_state.transcript[-1]
                    await self.ui.display_final_consensus(final_message.content)
                    
                    # Save final state
                    saved_path = self.logger.save_session(self.current_state)
                    await self.ui.send_output(f"Discussion saved to: {saved_path}")
                else:
                    # Advance to next round
                    old_round = self.current_state.current_round
                    self.current_state.current_round = Round(old_round.value + 1)
                    await self.ui.display_round_transition(old_round, self.current_state.current_round)
                    await asyncio.sleep(2)

async def handle_client_message(websocket: WebSocketServerProtocol, message: dict, ws_manager: WebSocketManager):
    """Handle incoming client messages"""
    try:
        command = message.get('command', '').strip()
        
        if command == '1':
            # Start new discussion
            await ws_manager.send_to_client(websocket, {
                'type': 'output',
                'content': 'Enter discussion topic:',
                'style': 'system-message'
            })
            await ws_manager.send_to_client(websocket, {
                'type': 'prompt',
                'prompt': 'Topic: '
            })
            
        elif command == '2':
            # Load previous discussion
            session_logger = SessionLogger()
            sessions = session_logger.list_sessions()
            
            if not sessions:
                await ws_manager.send_to_client(websocket, {
                    'type': 'output',
                    'content': 'No saved sessions found.',
                    'style': 'system-message'
                })
                await ws_manager.send_to_client(websocket, {
                    'type': 'menu'
                })
            else:
                await ws_manager.send_to_client(websocket, {
                    'type': 'output',
                    'content': 'Saved Sessions:',
                    'style': 'system-message'
                })
                
                for i, (filename, topic, timestamp) in enumerate(sessions[:10]):
                    await ws_manager.send_to_client(websocket, {
                        'type': 'output',
                        'content': f"{i+1}. [{timestamp[:10]}] {topic}",
                        'style': 'menu-option'
                    })
                
                await ws_manager.send_to_client(websocket, {
                    'type': 'output',
                    'content': "Select session number (or 'c' to cancel):",
                    'style': 'system-message'
                })
                
        elif command == '3':
            # Exit
            await ws_manager.send_to_client(websocket, {
                'type': 'output',
                'content': 'Thank you for using Roundtable!',
                'style': 'system-message'
            })
            await websocket.close()
            
        elif command == 'help':
            await ws_manager.send_to_client(websocket, {
                'type': 'menu'
            })
            
        elif command.startswith('Topic: '):
            # Extract topic and start discussion
            topic = command[7:].strip()
            if topic:
                session = WebRoundtableSession(ws_manager)
                ws_manager.current_session = session
                await session.run_discussion(topic)
            else:
                await ws_manager.send_to_client(websocket, {
                    'type': 'output',
                    'content': 'Please enter a valid topic.',
                    'style': 'error-message'
                })
        
        elif command.isdigit() and ws_manager.current_session is None:
            # Session selection
            session_logger = SessionLogger() 
            sessions = session_logger.list_sessions()
            idx = int(command) - 1
            
            if 0 <= idx < len(sessions):
                state = session_logger.load_session(sessions[idx][0])
                if state:
                    # Replay session (simplified for web)
                    await ws_manager.send_to_client(websocket, {
                        'type': 'clear'
                    })
                    
                    await ws_manager.send_to_client(websocket, {
                        'type': 'header',
                        'topic': state.topic,
                        'round': 'Replay'
                    })
                    
                    for msg in state.transcript:
                        await ws_manager.send_to_client(websocket, {
                            'type': 'message',
                            'participant_id': msg.participant_id,
                            'participant_model': msg.participant_model,
                            'content': msg.content,
                            'is_moderator': msg.role == Role.MODERATOR
                        })
                    
                    await ws_manager.send_to_client(websocket, {
                        'type': 'output',
                        'content': '\nPress Enter to return to menu...',
                        'style': 'system-message'
                    })
            else:
                await ws_manager.send_to_client(websocket, {
                    'type': 'output',
                    'content': 'Invalid selection.',
                    'style': 'error-message'
                })
        
        elif command.lower() == 'c':
            # Cancel - return to menu
            await ws_manager.send_to_client(websocket, {
                'type': 'menu'
            })
            
        elif not command:
            # Enter pressed - return to menu (for replay mode)
            await ws_manager.send_to_client(websocket, {
                'type': 'menu'
            })
        
        else:
            await ws_manager.send_to_client(websocket, {
                'type': 'output',
                'content': f'Unknown command: {command}',
                'style': 'error-message'
            })
            await ws_manager.send_to_client(websocket, {
                'type': 'menu'
            })
            
    except Exception as e:
        logger.error(f"Error handling command '{command}': {e}")
        await ws_manager.send_to_client(websocket, {
            'type': 'output',
            'content': f'Error: {str(e)}',
            'style': 'error-message'
        })

async def websocket_handler(websocket: WebSocketServerProtocol, path: str, ws_manager: WebSocketManager):
    """Handle WebSocket connections"""
    await ws_manager.register_client(websocket)
    
    try:
        async for raw_message in websocket:
            try:
                message = json.loads(raw_message)
                await handle_client_message(websocket, message, ws_manager)
            except json.JSONDecodeError:
                await ws_manager.send_to_client(websocket, {
                    'type': 'output',
                    'content': 'Invalid message format',
                    'style': 'error-message'
                })
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await ws_manager.send_to_client(websocket, {
                    'type': 'output',
                    'content': f'Error: {str(e)}',
                    'style': 'error-message'
                })
    
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        await ws_manager.unregister_client(websocket)

async def start_server(host='localhost', port=8000):
    """Start the WebSocket server"""
    ws_manager = WebSocketManager()
    
    logger.info(f"Starting Roundtable WebSocket server on {host}:{port}")
    
    async def handler(websocket, path):
        await websocket_handler(websocket, path, ws_manager)
    
    server = await websockets.serve(handler, host, port)
    logger.info(f"WebSocket server running on ws://{host}:{port}/ws")
    
    return server

if __name__ == "__main__":
    async def main():
        server = await start_server()
        await server.wait_closed()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")