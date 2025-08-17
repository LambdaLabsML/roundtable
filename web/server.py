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
        self.client_states: dict = {}  # Track state for each client
        
    def _get_client_key(self, websocket: WebSocketServerProtocol) -> str:
        """Get a stable key for the websocket"""
        return f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        
    async def register_client(self, websocket: WebSocketServerProtocol):
        """Register a new WebSocket client"""
        self.clients.add(websocket)
        logger.info(f"Client {websocket.remote_address} connected")
        
        # Don't send menu automatically - let client handle initial display
    
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
            logger.warning(f"Missing API keys: {', '.join(missing_keys)}")
            logger.warning("Please set up your API keys in a .env file")
            raise Exception(f"Missing API keys: {', '.join(missing_keys)}. Please create a .env file with your API keys.")
    
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
                    
                    # Return to main menu
                    await self.ui.send_output("", "")
                    await self.ui.send_output("Press Enter to return to main menu...", "system-message")
                    
                    # Clear the current session
                    self.ws_manager.current_session = None
                    
                    # Reset prompt to default
                    await ws_manager.send_to_client(websocket, {
                        'type': 'prompt',
                        'prompt': '$ '
                    })
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
        client_key = ws_manager._get_client_key(websocket)
        current_state = ws_manager.client_states.get(client_key, 'main_menu')
        print(f"DEBUG: Received command '{command}' from {websocket.remote_address}, current state: {current_state}")
        logger.info(f"Received command '{command}' from {websocket.remote_address}, current state: {current_state}")
        
        if command.isdigit():
            print(f"DEBUG: Command '{command}' is digit, checking session selection condition")
            client_key = ws_manager._get_client_key(websocket)
            current_state = ws_manager.client_states.get(client_key, 'main_menu')
            print(f"DEBUG: Client key: {client_key}, Current state: {current_state}")
            print(f"DEBUG: command.isdigit() = {command.isdigit()}")
            print(f"DEBUG: current_state == 'session_selection' = {current_state == 'session_selection'}")
            if current_state == 'session_selection':
                # Session selection
                print(f"DEBUG: Processing session selection: {command} for {websocket.remote_address}")
                logger.info(f"Processing session selection: {command} for {websocket.remote_address}")
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
                        
                        # Set state to waiting for Enter to return to menu
                        client_key = ws_manager._get_client_key(websocket)
                        ws_manager.client_states[client_key] = 'waiting_for_enter'
                        print(f"DEBUG: Session loaded, state set to waiting_for_enter for {websocket.remote_address}")
                else:
                    await ws_manager.send_to_client(websocket, {
                        'type': 'output',
                        'content': 'Invalid selection.',
                        'style': 'error-message'
                    })
                    
                    # Reset client state on invalid selection
                    client_key = ws_manager._get_client_key(websocket)
                    ws_manager.client_states[client_key] = 'main_menu'
            else:
                # Not in session selection mode, treat as main menu command
                print(f"DEBUG: Command '{command}' is digit but not in session_selection mode, treating as main menu")
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
                        # Set client state to session selection mode
                        client_key = ws_manager._get_client_key(websocket)
                        ws_manager.client_states[client_key] = 'session_selection'
                        print(f"DEBUG: Client state set to session_selection for {websocket.remote_address}")
                        logger.info(f"Client state set to session_selection for {websocket.remote_address}")
                        
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
                else:
                    await ws_manager.send_to_client(websocket, {
                        'type': 'output',
                        'content': f'Unknown command: {command}',
                        'style': 'error-message'
                    })
                    await ws_manager.send_to_client(websocket, {
                        'type': 'menu'
                    })
        
        elif command == '1':
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
                # Set client state to session selection mode
                client_key = ws_manager._get_client_key(websocket)
                ws_manager.client_states[client_key] = 'session_selection'
                print(f"DEBUG: Client state set to session_selection for {websocket.remote_address}")
                logger.info(f"Client state set to session_selection for {websocket.remote_address}")
                
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
            client_key = ws_manager._get_client_key(websocket)
            ws_manager.client_states[client_key] = 'main_menu'
            await ws_manager.send_to_client(websocket, {
                'type': 'menu'
            })
            
        elif command.startswith('Topic: '):
            # Extract topic and start discussion (legacy format)
            topic = command[7:].strip()
            if topic:
                try:
                    session = WebRoundtableSession(ws_manager)
                    ws_manager.current_session = session
                    await session.run_discussion(topic)
                except Exception as e:
                    logger.error(f"Error creating session: {e}")
                    await ws_manager.send_to_client(websocket, {
                        'type': 'output',
                        'content': f'Error starting discussion: {str(e)}',
                        'style': 'error-message'
                    })
                    await ws_manager.send_to_client(websocket, {
                        'type': 'menu'
                    })
            else:
                await ws_manager.send_to_client(websocket, {
                    'type': 'output',
                    'content': 'Please enter a valid topic.',
                    'style': 'error-message'
                })
        

        
        elif ws_manager.current_session is None and len(command) > 0 and not command.isdigit() and command not in ['1', '2', '3', 'help', 'c'] and ws_manager.client_states.get(ws_manager._get_client_key(websocket)) != 'session_selection':
            # Handle topic input directly (when not in a session and not a menu command)
            topic = command.strip()
            if topic:
                try:
                    session = WebRoundtableSession(ws_manager)
                    ws_manager.current_session = session
                    await session.run_discussion(topic)
                except Exception as e:
                    logger.error(f"Error creating session: {e}")
                    await ws_manager.send_to_client(websocket, {
                        'type': 'output',
                        'content': f'Error starting discussion: {str(e)}',
                        'style': 'error-message'
                    })
                    await ws_manager.send_to_client(websocket, {
                        'type': 'menu'
                    })
            else:
                await ws_manager.send_to_client(websocket, {
                    'type': 'output',
                    'content': 'Please enter a valid topic.',
                    'style': 'error-message'
                })
        
        elif command.lower() == 'c':
            # Cancel - return to menu
            client_key = ws_manager._get_client_key(websocket)
            ws_manager.client_states[client_key] = 'main_menu'
            await ws_manager.send_to_client(websocket, {
                'type': 'menu'
            })
            
        elif not command:
            # Enter pressed - return to menu (for replay mode or after discussion completion)
            print(f"DEBUG: Empty command received (Enter pressed) from {websocket.remote_address}")
            client_key = ws_manager._get_client_key(websocket)
            current_state = ws_manager.client_states.get(client_key, 'main_menu')
            print(f"DEBUG: Current state when Enter pressed: {current_state}")
            
            if current_state == 'waiting_for_enter':
                # User pressed Enter after viewing a session, return to main menu
                print(f"DEBUG: User pressed Enter in waiting_for_enter state, returning to main menu")
                ws_manager.client_states[client_key] = 'main_menu'
                await ws_manager.send_to_client(websocket, {
                    'type': 'menu'
                })
            else:
                # Default behavior for Enter in other states
                print(f"DEBUG: User pressed Enter in {current_state} state, returning to main menu")
                ws_manager.client_states[client_key] = 'main_menu'
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
    try:
        await ws_manager.register_client(websocket)
        logger.info(f"Client registered successfully: {websocket.remote_address}")
        
        async for raw_message in websocket:
            try:
                message = json.loads(raw_message)
                await handle_client_message(websocket, message, ws_manager)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                await ws_manager.send_to_client(websocket, {
                    'type': 'output',
                    'content': 'Invalid message format',
                    'style': 'error-message'
                })
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                await ws_manager.send_to_client(websocket, {
                    'type': 'output',
                    'content': f'Error: {str(e)}',
                    'style': 'error-message'
                })
    
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"Connection closed normally: {websocket.remote_address}")
    except Exception as e:
        logger.error(f"Unexpected error in websocket handler: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
    finally:
        await ws_manager.unregister_client(websocket)

async def start_server(host='localhost', port=8000):
    """Start the WebSocket server"""
    ws_manager = WebSocketManager()
    
    logger.info(f"Starting Roundtable WebSocket server on {host}:{port}")
    
    async def handler(websocket):
        await websocket_handler(websocket, "/ws", ws_manager)
    
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