"""
Real integration tests for Roundtable application using actual API keys.

These tests require real API keys to be set in environment variables:
- ANTHROPIC_API_KEY
- OPENAI_API_KEY  
- GOOGLE_API_KEY

Set SKIP_REAL_TESTS=1 to skip these tests if API keys are not available.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import asyncio
from datetime import datetime
from unittest.mock import patch
import logging

# Configure logging for tests
logging.basicConfig(level=logging.INFO)

def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line(
        "markers", "real_api: mark test as using real API calls"
    )

def check_api_keys_available():
    """Check if real API keys are available for testing"""
    required_keys = ["anthropic", "openai", "google"]
    missing_keys = []
    
    from config import API_KEYS

    for key in required_keys:
        if not API_KEYS[key]:
            missing_keys.append(key)
    
    if missing_keys:
        return False, missing_keys
    return True, []

def should_skip_real_tests():
    """Check if real tests should be skipped"""
    if os.getenv("SKIP_REAL_TESTS") == "1":
        return True, "SKIP_REAL_TESTS environment variable is set"
    
    available, missing = check_api_keys_available()
    if not available:
        return True, f"Missing API keys: {', '.join(missing)}. Set them in .env file or as environment variables."
    
    return False, None

# Skip condition
skip_reason_check = should_skip_real_tests()
skip_real_tests = skip_reason_check[0]
skip_reason = skip_reason_check[1] or "Skipping real API tests"

@pytest.mark.real_api
@pytest.mark.skipif(skip_real_tests, reason=skip_reason)
class TestRealAPIIntegration:
    """Real API integration tests"""
    
    def test_real_anthropic_client_initialization(self):
        """Test real Anthropic client initialization with actual API key"""
        from llm.anthropic_client import ClaudeClient
        from config import API_KEYS
        
        # Should not raise exception with real API key
        client = ClaudeClient(API_KEYS["anthropic"])
        assert client.client is not None
        assert hasattr(client.client, 'messages')
    
    def test_real_openai_client_initialization(self):
        """Test real OpenAI client initialization with actual API key"""
        from llm.openai_client import GPTClient
        from config import API_KEYS
        
        # Should not raise exception with real API key
        client = GPTClient(API_KEYS["openai"])
        assert client.client is not None
        assert hasattr(client.client, 'chat')
    
    def test_real_google_client_initialization(self):
        """Test real Google client initialization with actual API key"""
        from llm.google_client import GeminiClient
        from config import API_KEYS
        
        # Should not raise exception with real API key
        client = GeminiClient(API_KEYS["google"])
        assert client.model is not None
        assert hasattr(client.model, 'generate_content')
    
    @pytest.mark.asyncio
    async def test_real_anthropic_generate_response(self):
        """Test real Anthropic API call with simple prompt"""
        from llm.anthropic_client import ClaudeClient
        from config import API_KEYS
        
        client = ClaudeClient(API_KEYS["anthropic"])
        
        system_prompt = "You are a helpful assistant. Respond briefly."
        messages = [{"role": "user", "content": "Say hello in exactly 3 words."}]
        
        response = await client.generate_response(
            system_prompt=system_prompt,
            messages=messages,
            temperature=0.1,  # Low temperature for consistency
            max_tokens=2048  # Increased to avoid truncation
        )
        
        assert isinstance(response, str)
        assert len(response.strip()) > 0
        assert len(response.split()) <= 10  # Should be brief
    
    @pytest.mark.asyncio
    async def test_real_openai_generate_response(self):
        """Test real OpenAI API call with simple prompt"""
        from llm.openai_client import GPTClient
        from config import API_KEYS
        
        client = GPTClient(API_KEYS["openai"])
        
        system_prompt = "You are a helpful assistant. Respond briefly."
        messages = [{"role": "user", "content": "Say hello in exactly 3 words."}]
        
        response = await client.generate_response(
            system_prompt=system_prompt,
            messages=messages,
            max_tokens=2048  # Increased to give GPT-5 room to generate content
        )
        
        assert isinstance(response, str)
        assert len(response.strip()) > 0
        assert len(response.split()) <= 10  # Should be brief
    
    @pytest.mark.asyncio
    async def test_real_google_generate_response(self):
        """Test real Google API call with simple prompt"""
        from llm.google_client import GeminiClient
        from config import API_KEYS
        
        client = GeminiClient(API_KEYS["google"])
        
        system_prompt = "You are a helpful assistant. Respond briefly."
        messages = [{"role": "user", "content": "Say hello in exactly 3 words."}]
        
        response = await client.generate_response(
            system_prompt=system_prompt,
            messages=messages,
            temperature=0.1,  # Low temperature for consistency
            max_tokens=2048  # Increased to avoid truncation
        )
        
        assert isinstance(response, str)
        assert len(response.strip()) > 0
        assert len(response.split()) <= 10  # Should be brief
    
    @pytest.mark.asyncio
    async def test_real_discussion_flow(self):
        """Test a real mini discussion flow with actual API calls"""
        from models.discussion import DiscussionState, Round, Role, Message
        from moderator.turn_manager import TurnManager
        from llm.anthropic_client import ClaudeClient
        from config import API_KEYS
        import uuid
        
        # Initialize real client
        moderator_client = ClaudeClient(API_KEYS["anthropic"])
        turn_manager = TurnManager()
        
        # Create simple discussion state
        state = DiscussionState(
            id=str(uuid.uuid4()),
            topic="What is the capital of France?",  # Simple topic
            current_round=Round.AGENDA,
            current_speaker=None,
            turn_order=[],
            transcript=[],
            round_metadata={},
            status="in_progress",
            started_at=datetime.now(),
            completed_at=None
        )
        
        # Test moderator opening
        next_speaker = turn_manager.determine_next_speaker(state)
        assert next_speaker == "claude_moderator"
        
        # Generate real moderator response
        system_prompt = """You are a discussion moderator. Keep your responses very brief (1-2 sentences). 
Round: Agenda Setting
Your role: Set the agenda and introduce the simple question about the capital of France."""
        
        messages = [{"role": "user", "content": f"Let's discuss: {state.topic}"}]
        
        response = await moderator_client.generate_response(
            system_prompt=system_prompt,
            messages=messages,
            temperature=0.3,
            max_tokens=100
        )
        
        # Verify response
        assert isinstance(response, str)
        assert len(response.strip()) > 10
        assert len(response) < 500  # Keep it reasonable
        
        # Add to transcript
        message = Message(
            participant_id="claude_moderator",
            participant_model="Claude 4.1 Opus",
            role=Role.MODERATOR,
            round=Round.AGENDA,
            content=response,
            timestamp=datetime.now(),
            turn_number=0
        )
        
        state.transcript.append(message)
        
        # Test round advancement logic
        should_advance = turn_manager.should_advance_round(state)
        assert should_advance is True  # Should advance after moderator speaks in agenda

@pytest.mark.real_api 
@pytest.mark.skipif(skip_real_tests, reason=skip_reason)
class TestRealErrorHandling:
    """Test error handling with real API calls"""
    
    @pytest.mark.asyncio
    async def test_real_api_error_handling(self):
        """Test handling of real API errors (rate limits, invalid requests)"""
        from llm.anthropic_client import ClaudeClient
        from config import API_KEYS
        
        client = ClaudeClient(API_KEYS["anthropic"])
        
        # Test with invalid message format (should raise ValueError)
        with pytest.raises(ValueError, match="Messages list cannot be empty"):
            await client.generate_response(
                system_prompt="Test",
                messages=[],  # Empty messages should fail
                max_tokens=50
            )
        
        # Test with invalid message structure
        with pytest.raises(ValueError, match="Message 0 must be a dictionary"):
            await client.generate_response(
                system_prompt="Test",
                messages=["invalid"],  # Should be dict, not string
                max_tokens=50
            )
    
    def test_invalid_api_key_handling(self):
        """Test handling of invalid API keys"""
        from llm.anthropic_client import ClaudeClient
        
        # Test with obviously invalid key
        with pytest.raises(ValueError, match="Invalid Anthropic API key"):
            ClaudeClient("invalid_key")
        
        with pytest.raises(ValueError, match="Invalid Anthropic API key"):
            ClaudeClient("your_anthropic_api_key_here")

def test_skip_conditions():
    """Test that skip conditions work properly"""
    # This test always runs to verify skip logic
    available, missing = check_api_keys_available()
    skip, reason = should_skip_real_tests()
    
    if skip:
        print(f"Real tests would be skipped: {reason}")
    else:
        print("Real tests would run - API keys are available")
    
    # This should always pass
    assert isinstance(skip, bool)
    assert isinstance(reason, (str, type(None)))