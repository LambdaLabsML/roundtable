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


## Fix issues using the Claude Code GitHub Action

This repository includes a ready-to-use workflow that lets you ask Claude to propose fixes via GitHub comments.

How it works
- The workflow is defined at .github/workflows/claude.yml and uses anthropics/claude-code-action@beta
- It listens to the following events when the text contains "@claude":
  - New issue body
  - Issue comment
  - Pull request review comment
  - Pull request review submission
- When triggered, Claude analyzes the repository and your request for up to 60 minutes and proposes changes

Prerequisites
- In your GitHub repository settings, add one of the following secrets:
  - ANTHROPIC_API_KEY: an Anthropic API key with access to Claude
  - OR set CLAUDE_CODE_OAUTH_TOKEN if you are using the OAuth-based setup (see action docs)

How to trigger a fix
1. Open or comment on an issue describing the problem, and mention Claude with clear instructions. For example:
   - "@claude update README to explain how to fix issues using the Claude Code GitHub Action"
   - "@claude fix failing tests in tests/ and explain the changes"
2. Or, on a pull request, leave a review comment with an @claude mention and what you want fixed
3. Monitor the action run under the Actions tab; it will respond in the thread and/or create a proposed change depending on repository permissions

Tips
- Be specific about the desired outcome and any constraints (e.g., file paths, style, tests)
- If the action doesn’t respond, verify:
  - The mention includes exactly "@claude"
  - Repository Actions are enabled
  - Required secret (ANTHROPIC_API_KEY or CLAUDE_CODE_OAUTH_TOKEN) is present

Security and network access
- The workflow is configured with minimal permissions and supports optional network domain allowlisting. See the commented experimental_allowed_domains section in .github/workflows/claude.yml if you need to restrict outbound requests.

## Notes

- Uses GPT-5 (gpt-5-2025-08-07)
- Gemini 2.5 Pro falls back to Gemini Pro if not available
- Discussion time varies based on API response times (typically 5-10 minutes)
