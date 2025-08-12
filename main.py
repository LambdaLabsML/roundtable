import asyncio
import uuid
from datetime import datetime
from typing import Optional
from models.discussion import DiscussionState, Round, Message, Role
from llm.anthropic_client import ClaudeClient
from llm.openai_client import GPTClient
from llm.google_client import GeminiClient
from moderator.turn_manager import TurnManager
from ui.terminal import TerminalUI
from storage.session_logger import SessionLogger
from config import API_KEYS
import signal
import sys
import traceback

class RoundtableApp:
    def __init__(self):
        self.ui = TerminalUI()
        self.logger = SessionLogger()
        self.turn_manager = TurnManager()
        
        # Check API keys before initializing
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
            self.ui.console.print(f"[red]Error initializing LLM clients: {e}[/red]")
            self.ui.console.print("[yellow]Please check your API keys in .env file[/yellow]")
            sys.exit(1)
        
        self.participant_models = {
            "claude_moderator": "Claude 4.1 Opus",
            "claude": "Claude 4.1 Opus",
            "gpt5": "GPT-5 Thinking",
            "gemini": "Gemini 2.5 Pro"
        }
        
        self.current_session_file = None
        
        # Handle Ctrl+C gracefully
        signal.signal(signal.SIGINT, self.handle_interrupt)
    
    def check_api_keys(self):
        """Check if API keys are set"""
        missing_keys = []
        for service, key in API_KEYS.items():
            if not key or key == f"your_{service}_api_key_here":
                missing_keys.append(service.upper())
        
        if missing_keys:
            self.ui.console.print(f"[red]Missing API keys: {', '.join(missing_keys)}[/red]")
            self.ui.console.print("[yellow]Please set them in the .env file[/yellow]")
            sys.exit(1)
    
    def handle_interrupt(self, signum, frame):
        """Handle interrupt signal"""
        self.ui.console.print("\n[yellow]Interrupted. Exiting...[/yellow]")
        sys.exit(0)
    
    def load_prompts(self) -> tuple[str, str]:
        """Load prompt templates"""
        try:
            with open('prompts/moderator.txt', 'r') as f:
                moderator_prompt = f.read()
            with open('prompts/panelist.txt', 'r') as f:
                panelist_prompt = f.read()
            return moderator_prompt, panelist_prompt
        except FileNotFoundError as e:
            self.ui.console.print(f"[red]Error loading prompts: {e}[/red]")
            sys.exit(1)
    
    async def generate_response(
        self,
        participant_id: str,
        state: DiscussionState,
        is_moderator: bool = False
    ) -> str:
        """Generate response from LLM with better error handling"""
        moderator_prompt, panelist_prompt = self.load_prompts()
        
        # Prepare conversation history
        history = []
        for msg in state.transcript:
            history.append({
                "role": "assistant" if msg.participant_id == participant_id else "user",
                "content": f"[{msg.participant_model}]: {msg.content}"
            })
        
        # If this is the first message in the discussion, add a default user message
        if not history:
            history.append({
                "role": "user",
                "content": f"Let's begin the discussion on: {state.topic}"
            })
        
        # Select appropriate prompt
        if is_moderator:
            system_prompt = moderator_prompt.format(
                round=state.current_round.value,
                round_name=self.ui.round_names[state.current_round]
            )
        else:
            system_prompt = panelist_prompt.format(
                round=state.current_round.value,
                round_name=self.ui.round_names[state.current_round]
            )
        
        # Generate response with error details
        client = self.clients[participant_id]
        
        try:
            response = await client.generate_response(
                system_prompt=system_prompt,
                messages=history,
                temperature=0.7
            )
            return response
        except Exception as e:
            self.ui.console.print(f"[red]Error from {participant_id}: {str(e)}[/red]")
            self.ui.console.print(f"[yellow]Error type: {type(e).__name__}[/yellow]")
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
            self.ui.clear_screen()
            self.ui.display_header(topic, self.current_state.current_round)
            
            # Show recent messages (last 3)
            for msg in self.current_state.transcript[-3:]:
                self.ui.display_message(msg)
            
            # Determine next speaker
            next_speaker = self.turn_manager.determine_next_speaker(self.current_state)
            self.current_state.current_speaker = next_speaker
            
            # Generate response
            self.ui.display_thinking(next_speaker)
            
            is_moderator = next_speaker == "claude_moderator"
            
            try:
                response = await self.generate_response(
                    next_speaker,
                    self.current_state,
                    is_moderator
                )
                retry_count = 0  # Reset retry count on success
            except Exception as e:
                retry_count += 1
                self.ui.console.print(f"[red]Error generating response (attempt {retry_count}/{max_retries}): {e}[/red]")
                
                if retry_count >= max_retries:
                    self.ui.console.print("[red]Max retries exceeded. Exiting.[/red]")
                    return
                
                self.ui.console.print(f"[yellow]Retrying in 3 seconds...[/yellow]")
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
                    self.ui.display_final_consensus(final_message.content)
                    
                    # Save final state
                    saved_path = self.logger.save_session(self.current_state)
                    self.ui.console.print(f"\n[green]Discussion saved to: {saved_path}[/green]")
                else:
                    # Advance to next round
                    old_round = self.current_state.current_round
                    self.current_state.current_round = Round(old_round.value + 1)
                    self.ui.display_round_transition(old_round, self.current_state.current_round)
                    await asyncio.sleep(2)
    
    def replay_discussion(self, state: DiscussionState):
        """Replay a saved discussion"""
        self.ui.clear_screen()
        self.ui.display_header(state.topic, Round.CONVERGENCE)
        
        current_round = Round.AGENDA
        for i, msg in enumerate(state.transcript):
            if msg.round != current_round:
                current_round = msg.round
                self.ui.console.print(f"\n[bold]═══ {self.ui.round_names[current_round]} ═══[/bold]\n")
            
            self.ui.display_message(msg)
            
            # Check if we're at the final synthesis (convergence round)
            is_final_synthesis = current_round == Round.CONVERGENCE
            
            # Check if this is the last message in the final synthesis round
            is_last_message_in_final = (is_final_synthesis and 
                                      i == len(state.transcript) - 1)
            
            if is_last_message_in_final:
                # Final synthesis page - show enter to go back
                input("\n[Press Enter to go back to main menu...]")
                break
            else:
                # Not final synthesis - allow space to continue or F to fast forward
                prompt = "\n[Press Space to continue, F to fast forward to final synthesis...]"
                user_input = input(prompt).strip().lower()
                
                if user_input == 'f':
                    # Fast forward to final synthesis
                    # Find the first message in the convergence round
                    for j, future_msg in enumerate(state.transcript[i+1:], i+1):
                        if future_msg.round == Round.CONVERGENCE:
                            # Clear screen and show header for convergence round
                            self.ui.clear_screen()
                            self.ui.display_header(state.topic, Round.CONVERGENCE)
                            self.ui.console.print(f"\n[bold]═══ {self.ui.round_names[Round.CONVERGENCE]} ═══[/bold]\n")
                            
                            # Display all convergence messages
                            convergence_messages = [m for m in state.transcript[j:] if m.round == Round.CONVERGENCE]
                            for conv_msg in convergence_messages:
                                self.ui.display_message(conv_msg)
                            
                            # Show final consensus if available
                            if state.status == "completed" and state.round_metadata.get("consensus"):
                                self.ui.display_final_consensus(state.round_metadata["consensus"])
                            
                            # Final synthesis page - show enter to go back
                            input("\n[Press Enter to go back to main menu...]")
                            return
                    
                    # If no convergence round found, show message and continue normally
                    self.ui.console.print("[yellow]No final synthesis found in this session.[/yellow]")
                    continue
        
        # Show final consensus if available (for cases where we didn't fast forward)
        if state.status == "completed" and state.round_metadata.get("consensus"):
            self.ui.display_final_consensus(state.round_metadata["consensus"])
    
    async def main_loop(self):
        """Main application loop"""
        while True:
            choice = self.ui.display_menu()
            
            if choice == "1":
                # New discussion
                topic = self.ui.get_topic_input()
                await self.run_discussion(topic)
                input("\n[Press Enter to return to menu...]")
            
            elif choice == "2":
                # Load previous discussion
                sessions = self.logger.list_sessions()
                if not sessions:
                    self.ui.console.print("[yellow]No saved sessions found.[/yellow]")
                    input("\n[Press Enter to continue...]")
                    continue
                
                # Display sessions
                self.ui.console.print("\n[bold]Saved Sessions:[/bold]\n")
                for i, (filename, topic, timestamp) in enumerate(sessions[:10]):
                    self.ui.console.print(f"{i+1}. [{timestamp[:10]}] {topic}")
                
                selection = input("\nSelect session number (or 'c' to cancel): ")
                if selection.lower() != 'c' and selection.isdigit():
                    idx = int(selection) - 1
                    if 0 <= idx < len(sessions):
                        state = self.logger.load_session(sessions[idx][0])
                        if state:
                            self.replay_discussion(state)
                        input("\n[Press Enter to return to menu...]")
            
            elif choice == "3":
                # Exit
                self.ui.console.print("[green]Thank you for using Roundtable![/green]")
                break

if __name__ == "__main__":
    app = RoundtableApp()
    asyncio.run(app.main_loop())
