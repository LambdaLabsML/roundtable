# Roundtable - LLM Socratic Discussion

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


## Fix an issue using OpenHands Agent

You can also use OpenHands agent to fix an issue for you. To trigger the agent, you can leave a comment in the issue thread, with the following format:

`@<agent-name> fix this issue`

For example, to use `openhands-claude` to fix an issue, you can leave a comment like this:

`@openhands-claude fix this issue`

The available agents are:
- `openhands-claude`
- `openhands-gemini`
- `openhands-gpt`

The GitHub actions for these agents are located in `.github/workflows`.

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

## Using OpenHands Agents to Fix Issues

This repository is equipped with automated OpenHands agents that can help fix issues and implement features. Three different agents are available, each powered by different AI models:

### Available Agents

- **@openhands-claude** - Powered by Anthropic's Claude Sonnet 4
- **@openhands-gemini** - Powered by Google's Gemini 2.5 Pro
- **@openhands-gpt** - Powered by OpenAI's GPT-5

### How to Use

To request an agent to work on an issue, simply mention the agent in a comment on any GitHub issue or pull request:

```
@openhands-claude fix this issue
```

```
@openhands-gemini please implement this feature
```

```
@openhands-gpt help resolve this bug
```

### Agent Capabilities

The OpenHands agents can:
- Analyze code and identify bugs
- Implement new features
- Write and run tests
- Update documentation
- Create pull requests with fixes
- Respond to code review feedback

### Configuration

The agents are configured through GitHub Actions workflows located in `.github/workflows/`:
- `openhands-claude.yml` - Claude agent configuration
- `openhands-gemini.yml` - Gemini agent configuration
- `openhands-gpt.yml` - GPT agent configuration

Each agent runs with appropriate permissions to read issues, create branches, and submit pull requests.

## Notes

- Uses GPT-5 (gpt-5-2025-08-07)
- Gemini 2.5 Pro falls back to Gemini Pro if not available
- Discussion time varies based on API response times (typically 5-10 minutes)
