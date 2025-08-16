import os
import sys
import termios
import tty
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown
from rich.prompt import Prompt
from models.discussion import DiscussionState, Round, Message

class TerminalUI:
    def __init__(self):
        self.console = Console()
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
            "deepseek": "blue",
            "claude_moderator": "magenta"
        }
    
    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def display_header(self, topic: str, current_round: Round):
        """Display discussion header"""
        self.console.print("\n[bold white]═══ ROUNDTABLE ═══[/bold white]\n", justify="center")
        self.console.print(f"[dim]Topic:[/dim] [bold]{topic}[/bold]\n", justify="center")
        
        progress_bar = ""
        for r in Round:
            if r.value < current_round.value:
                progress_bar += "●"
            elif r.value == current_round.value:
                progress_bar += "◉"
            else:
                progress_bar += "○"
            if r.value < 3:
                progress_bar += " "
        
        self.console.print(f"[bold]{self.round_names[current_round]}[/bold]", justify="center")
        self.console.print(f"[dim]{progress_bar}[/dim]\n", justify="center")
        self.console.print("─" * 80)
    
    def display_message(self, message: Message):
        """Display a single message"""
        color = self.participant_colors.get(message.participant_id, "white")
        role_badge = "🎯 MOD" if message.role.value == "moderator" else "💭"
        
        panel_title = f"{role_badge} {message.participant_model}"
        content = Markdown(message.content)
        
        panel = Panel(
            content,
            title=panel_title,
            title_align="left",
            border_style=color,
            padding=(1, 2)
        )
        self.console.print(panel)
        self.console.print()
    
    def display_thinking(self, participant: str):
        """Show thinking indicator"""
        color = self.participant_colors.get(participant, "white")
        self.console.print(f"[{color}]{participant}[/{color}] is formulating response...")
    
    def display_round_transition(self, from_round: Round, to_round: Round):
        """Display round transition"""
        self.console.print("\n" + "="*80)
        self.console.print(
            f"[bold green]✓ Completed:[/bold green] {self.round_names[from_round]}"
        )
        self.console.print(
            f"[bold blue]→ Starting:[/bold blue] {self.round_names[to_round]}"
        )
        self.console.print("="*80 + "\n")
    
    def get_topic_input(self) -> str:
        """Get discussion topic from user"""
        self.clear_screen()
        self.console.print("\n[bold white]═══ ROUNDTABLE ═══[/bold white]\n", justify="center")
        self.console.print("[dim]A Socratic discussion platform for LLMs[/dim]\n", justify="center")
        
        topic = Prompt.ask("\n[bold cyan]Enter discussion topic[/bold cyan]")
        return topic
    
    def display_menu(self) -> str:
        """Display main menu"""
        self.clear_screen()
        self.console.print("\n[bold white]═══ ROUNDTABLE ═══[/bold white]\n", justify="center")
        
        table = Table(show_header=False, box=None)
        table.add_column("Option", style="cyan", width=3)
        table.add_column("Description")
        
        table.add_row("1", "Start New Discussion")
        table.add_row("2", "Load Previous Discussion")
        table.add_row("3", "Exit")
        
        self.console.print(table)
        choice = Prompt.ask("\n[bold]Select option[/bold]", choices=["1", "2", "3"])
        return choice
    
    def display_final_consensus(self, consensus: str):
        """Display final consensus"""
        self.console.print("\n" + "="*80)
        self.console.print("[bold green]═══ FINAL CONSENSUS ═══[/bold green]", justify="center")
        self.console.print("="*80 + "\n")
        
        panel = Panel(
            Markdown(consensus),
            border_style="green",
            padding=(1, 2)
        )
        self.console.print(panel)
    
    def get_single_keypress(self) -> str:
        """Get a single keypress without requiring Enter"""
        if os.name == 'nt':  # Windows
            import msvcrt
            return msvcrt.getch().decode('utf-8').lower()
        else:  # Unix/Linux/macOS
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(sys.stdin.fileno())
                ch = sys.stdin.read(1).lower()
                return ch
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
