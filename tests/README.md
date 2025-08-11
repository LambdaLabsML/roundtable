# Testing Roundtable

## Quick Start

### 1. Install test dependencies
```bash
pip install pytest
```

### 2. Run tests
```bash
pytest tests/ -v
```

## Test Coverage

### Mock Tests (`test_basic.py`)
The mock test suite covers:
- ✅ Model creation (Role, Round, Message, DiscussionState)
- ✅ Turn manager logic
- ✅ Session saving and loading
- ✅ Configuration loading
- ✅ LLM client initialization (mocked)

### Real Integration Tests (`test_real_integration.py`)
The real integration test suite covers:
- ✅ Real API client initialization with actual API keys
- ✅ Real API calls to Anthropic, OpenAI, and Google
- ✅ Real discussion flow with actual LLM responses
- ✅ Error handling with real API responses
- ✅ API key validation and security

## GitHub Actions

Tests run automatically on:
- Every push to `main`
- Every pull request

### Python Versions Tested
- Python 3.10
- Python 3.11
- Python 3.12
- Python 3.13

### Platform
- macOS (latest)

## Running Tests Locally

### Mock Tests (Default)
```bash
# Run all mock tests (default)
pytest

# Verbose output
pytest -v

# Run specific test
pytest tests/test_basic.py::test_message_creation -v

# Show print statements
pytest -s

# Stop on first failure
pytest -x
```

### Real Integration Tests

**Prerequisites:** Set up your API keys in `.env` file or environment variables:
```bash
cp .env.template .env
# Edit .env with your real API keys
```

**Run real integration tests:**
```bash
# Using the helper script (recommended)
python run_real_tests.py

# Or run directly with pytest
pytest tests/test_real_integration.py -v -m real_api

# Run both mock and real tests
pytest -m "mock_api or real_api" -v
```

**Environment Variables:**
- `ANTHROPIC_API_KEY`: Your Anthropic API key
- `OPENAI_API_KEY`: Your OpenAI API key  
- `GOOGLE_API_KEY`: Your Google API key
- `SKIP_REAL_TESTS=1`: Skip real tests even if API keys are available

## Test Structure

```
tests/
├── __init__.py                # Package marker
├── test_basic.py             # Mock tests (no real API calls)
├── test_real_integration.py  # Real integration tests (requires API keys)
└── README.md                 # This documentation
```

**Additional Files:**
- `pytest.ini` - Test configuration and markers
- `run_real_tests.py` - Helper script for running real tests

## Adding New Tests

### Mock Tests
Add new mock test functions to `test_basic.py`:

```python
@pytest.mark.mock_api  # Optional marker
def test_your_feature():
    """Test description"""
    # Your test code with mocked APIs
    assert expected == actual
```

### Real Integration Tests  
Add new real test functions to `test_real_integration.py`:

```python
@pytest.mark.real_api
@pytest.mark.skipif(skip_real_tests, reason=skip_reason)
class TestYourRealFeature:
    @pytest.mark.asyncio
    async def test_real_feature(self):
        """Test with real API calls"""
        from config import API_KEYS
        # Your test code with real APIs
        assert expected == actual
```

## Test Types

### Mock Tests (Default)
Mock tests use `@patch` decorators to mock external API calls:

```python
@pytest.mark.mock_api
@patch('anthropic.Anthropic')
def test_with_mocked_api(mock_anthropic):
    mock_anthropic.return_value = MagicMock()
    # Your test code
```

### Real Integration Tests
Real tests use actual API keys and make real API calls:

```python
@pytest.mark.real_api
@pytest.mark.asyncio
async def test_real_api_call():
    from config import API_KEYS
    client = ClaudeClient(API_KEYS["anthropic"])
    response = await client.generate_response(...)
    assert isinstance(response, str)
```