"""Minimal mock tests for Roundtable application"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

# Test imports work correctly
def test_imports():
    """Test that all modules can be imported"""
    try:
        from models.discussion import Role, Round, Message, DiscussionState
        from moderator.turn_manager import TurnManager
        from storage.session_logger import SessionLogger
        from ui.terminal import TerminalUI
        assert True
    except ImportError as e:
        pytest.fail(f"Import failed: {e}")

def test_role_enum():
    """Test Role enum values"""
    from models.discussion import Role
    
    assert Role.MODERATOR.value == "moderator"
    assert Role.PANELIST.value == "panelist"

def test_round_enum():
    """Test Round enum values"""
    from models.discussion import Round
    
    assert Round.AGENDA.value == 0
    assert Round.EVIDENCE.value == 1
    assert Round.CROSS_EXAMINATION.value == 2
    assert Round.CONVERGENCE.value == 3

def test_message_creation():
    """Test Message creation"""
    from models.discussion import Message, Role, Round
    
    msg = Message(
        participant_id="test_id",
        participant_model="Test Model",
        role=Role.PANELIST,
        round=Round.AGENDA,
        content="Test content",
        timestamp=datetime.now(),
        turn_number=0
    )
    
    assert msg.participant_id == "test_id"
    assert msg.participant_model == "Test Model"
    assert msg.content == "Test content"

def test_discussion_state():
    """Test DiscussionState creation"""
    from models.discussion import DiscussionState, Round
    
    state = DiscussionState(
        id="test-uuid",
        topic="AI Ethics",
        current_round=Round.AGENDA,
        current_speaker=None,
        turn_order=[],
        transcript=[],
        round_metadata={},
        status="in_progress",
        started_at=datetime.now(),
        completed_at=None
    )
    
    assert state.topic == "AI Ethics"
    assert state.status == "in_progress"
    assert state.current_round == Round.AGENDA

def test_turn_manager_initialization():
    """Test TurnManager initialization"""
    from moderator.turn_manager import TurnManager
    
    manager = TurnManager()
    assert manager.moderator_id == "claude_moderator"
    assert "gpt5" in manager.panelist_ids
    assert "claude" in manager.panelist_ids
    assert "gemini" in manager.panelist_ids
    assert "deepseek" in manager.panelist_ids

def test_turn_manager_agenda_speaker():
    """Test that moderator speaks first in agenda round"""
    from moderator.turn_manager import TurnManager
    from models.discussion import DiscussionState, Round
    
    manager = TurnManager()
    state = DiscussionState(
        id="test",
        topic="Test",
        current_round=Round.AGENDA,
        current_speaker=None,
        turn_order=[],
        transcript=[],
        round_metadata={},
        status="in_progress",
        started_at=datetime.now(),
        completed_at=None
    )
    
    next_speaker = manager.determine_next_speaker(state)
    assert next_speaker == "claude_moderator"

def test_turn_manager_round_advancement():
    """Test round advancement logic"""
    from moderator.turn_manager import TurnManager
    from models.discussion import DiscussionState, Round, Message, Role
    
    manager = TurnManager()
    state = DiscussionState(
        id="test",
        topic="Test",
        current_round=Round.AGENDA,
        current_speaker=None,
        turn_order=[],
        transcript=[],
        round_metadata={},
        status="in_progress",
        started_at=datetime.now(),
        completed_at=None
    )
    
    # Should not advance without moderator message
    assert not manager.should_advance_round(state)
    
    # Add moderator message
    state.transcript.append(
        Message(
            participant_id="claude_moderator",
            participant_model="Claude",
            role=Role.MODERATOR,
            round=Round.AGENDA,
            content="Welcome to the discussion",
            timestamp=datetime.now(),
            turn_number=0
        )
    )
    
    # Now should advance
    assert manager.should_advance_round(state)

def test_session_logger_initialization(tmp_path):
    """Test SessionLogger initialization"""
    from storage.session_logger import SessionLogger
    
    sessions_dir = tmp_path / "test_sessions"
    logger = SessionLogger(str(sessions_dir))
    
    assert sessions_dir.exists()

def test_session_save_and_load(tmp_path):
    """Test saving and loading sessions"""
    from storage.session_logger import SessionLogger
    from models.discussion import DiscussionState, Message, Round, Role
    
    sessions_dir = tmp_path / "test_sessions"
    logger = SessionLogger(str(sessions_dir))
    
    # Create test state
    state = DiscussionState(
        id="test-123",
        topic="Climate Change",
        current_round=Round.EVIDENCE,
        current_speaker="gpt5",
        turn_order=["gpt5", "claude", "gemini"],
        transcript=[
            Message(
                participant_id="claude_moderator",
                participant_model="Claude Moderator",
                role=Role.MODERATOR,
                round=Round.AGENDA,
                content="Let's discuss climate change",
                timestamp=datetime.now(),
                turn_number=0
            )
        ],
        round_metadata={"test": "data"},
        status="in_progress",
        started_at=datetime.now(),
        completed_at=None
    )
    
    # Save session
    saved_path = logger.save_session(state)
    assert Path(saved_path).exists()
    
    # Load session
    filename = Path(saved_path).name
    loaded_state = logger.load_session(filename)
    
    assert loaded_state is not None
    assert loaded_state.topic == "Climate Change"
    assert loaded_state.id == "test-123"
    assert len(loaded_state.transcript) == 1

@pytest.mark.mock_api
@patch('anthropic.Anthropic')
@patch('openai.OpenAI')
@patch('google.generativeai.configure')
@patch('google.generativeai.GenerativeModel')
def test_llm_client_initialization_mocked(mock_gemini_model, mock_gemini_config, mock_openai, mock_anthropic):
    """Test that LLM clients can be initialized with mocked APIs"""
    # Mock the API clients
    mock_anthropic.return_value = MagicMock()
    mock_openai.return_value = MagicMock()
    mock_gemini_model.return_value = MagicMock()
    
    # Test imports and initialization
    from llm.anthropic_client import ClaudeClient
    from llm.openai_client import GPTClient
    from llm.google_client import GeminiClient
    from llm.lambda_client import LambdaClient
    
    # These should not raise errors with valid keys
    claude = ClaudeClient("sk-ant-api03-valid-key-for-testing")
    assert claude.client is not None
    
    gpt = GPTClient("sk-valid-key-for-testing")
    assert gpt.client is not None
    
    gemini = GeminiClient("AIza-valid-key-for-testing")
    assert gemini.model is not None

    # Test Lambda client initialization
    lambda_client = LambdaClient("lambda-valid-key-for-testing")
    assert lambda_client.api_key == "lambda-valid-key-for-testing"
    assert lambda_client.model == "deepseek-llama3.3-70b"

def test_config_loading():
    """Test configuration loading"""
    import os
    from unittest.mock import patch
    
    # Mock environment variables
    with patch.dict(os.environ, {
        'ANTHROPIC_API_KEY': 'test_anthropic',
        'OPENAI_API_KEY': 'test_openai',
        'GOOGLE_API_KEY': 'test_google',
        'LAMBDA_API_KEY': 'test_lambda'
    }):
        # Reimport config to get mocked values
        import importlib
        import config
        importlib.reload(config)
        
        assert config.API_KEYS['anthropic'] == 'test_anthropic'
        assert config.API_KEYS['openai'] == 'test_openai'
        assert config.API_KEYS['google'] == 'test_google'
        assert config.API_KEYS['lambda'] == 'test_lambda'

@pytest.mark.mock_api
@patch('requests.post')
def test_lambda_client_generate_response(mock_post):
    """Test Lambda client response generation with mocked HTTP requests"""
    from llm.lambda_client import LambdaClient
    import asyncio

    # Mock successful response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "This is a test response from DeepSeek"
                }
            }
        ]
    }
    mock_post.return_value = mock_response

    # Test client
    client = LambdaClient("test-lambda-key")

    # Test response generation
    async def test_generate():
        response = await client.generate_response(
            system_prompt="You are a helpful assistant",
            messages=[{"role": "user", "content": "Hello"}],
            temperature=0.7,
            max_tokens=100
        )
        return response

    result = asyncio.run(test_generate())
    assert result == "This is a test response from DeepSeek"

    # Verify the request was made correctly
    mock_post.assert_called_once()
    call_args = mock_post.call_args
    assert call_args[0][0] == "https://api.lambda.ai/v1/chat/completions"
    assert call_args[1]["headers"]["Authorization"] == "Bearer test-lambda-key"
    assert call_args[1]["json"]["model"] == "deepseek-llama3.3-70b"

def test_deepseek_integration_in_discussion():
    """Test that DeepSeek is properly integrated into the discussion flow"""
    from moderator.turn_manager import TurnManager
    from models.discussion import DiscussionState, Round, Message, Role

    manager = TurnManager()
    state = DiscussionState(
        id="test",
        topic="AI Ethics",
        current_round=Round.EVIDENCE,
        current_speaker=None,
        turn_order=[],
        transcript=[],
        round_metadata={},
        status="in_progress",
        started_at=datetime.now(),
        completed_at=None
    )

    # Simulate other participants having spoken
    state.transcript.extend([
        Message(
            participant_id="gpt5",
            participant_model="GPT-5",
            role=Role.PANELIST,
            round=Round.EVIDENCE,
            content="GPT-5 evidence",
            timestamp=datetime.now(),
            turn_number=0
        ),
        Message(
            participant_id="claude",
            participant_model="Claude",
            role=Role.PANELIST,
            round=Round.EVIDENCE,
            content="Claude evidence",
            timestamp=datetime.now(),
            turn_number=1
        ),
        Message(
            participant_id="gemini",
            participant_model="Gemini",
            role=Role.PANELIST,
            round=Round.EVIDENCE,
            content="Gemini evidence",
            timestamp=datetime.now(),
            turn_number=2
        )
    ])

    # DeepSeek should be able to speak next
    next_speaker = manager.determine_next_speaker(state)
    assert next_speaker == "deepseek"

    # Add DeepSeek's message
    state.transcript.append(
        Message(
            participant_id="deepseek",
            participant_model="DeepSeek-Llama3.3-70B",
            role=Role.PANELIST,
            round=Round.EVIDENCE,
            content="DeepSeek evidence",
            timestamp=datetime.now(),
            turn_number=3
        )
    )

    # Now all panelists have spoken, should advance round
    assert manager.should_advance_round(state)
