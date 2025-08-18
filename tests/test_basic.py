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
    
    lambda_client = LambdaClient("lambda-valid-key-for-testing")
    assert lambda_client.client is not None

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