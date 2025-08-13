# Roundtable - LLM Socratic Discussion Platform

A Python terminal application that orchestrates structured, truth-seeking discussions between multiple LLMs.

## Features
- Structured 4-round Socratic discussions
- Three AI panelists (GPT-5, Claude 4.1, Gemini 2.5 Pro) with a Claude moderator
- Automatic session saving and replay functionality
- Clean terminal UI with rich formatting
- Graceful error handling and interruption support

## Installation

1. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up API keys:
```bash
cp .env.template .env
# Edit .env and add your API keys
```

## Usage

Run the application:
```bash
python main.py
```

## Discussion Structure

1. **Round 0 - Agenda Framing**: Moderator introduces the topic
2. **Round 1 - Evidence**: Each panelist presents initial perspectives
3. **Round 2 - Cross-examination**: Panelists review each other's arguments
4. **Round 3 - Convergence**: Consensus building through mini-Delphi process

## Session Management

- Sessions are automatically saved to the `sessions/` directory when discussions complete
- Load and replay previous discussions from the main menu
- **Session Replay Hotkeys:**
  - **Space**: Continue to next message (single keypress)
  - **F**: Fast forward to final synthesis (single keypress)
  - **Enter**: Return to main menu (from final synthesis page)
- Ctrl+C exits the application

## Requirements

- Python 3.8+
- API keys for Anthropic, OpenAI, and Google AI
- Terminal with Unicode support for best display

## Troubleshooting

If you encounter API errors:
1. Verify your API keys in `.env`
2. Check your API rate limits and quotas
3. The app will automatically retry failed requests with exponential backoff

## Notes

- Uses GPT-5 (gpt-5-2025-08-07)
- Gemini 2.5 Pro falls back to Gemini Pro if not available
- Discussion time varies based on API response times (typically 5-10 minutes)
