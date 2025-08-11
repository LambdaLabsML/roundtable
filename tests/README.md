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

The minimal test suite covers:
- ✅ Model creation (Role, Round, Message, DiscussionState)
- ✅ Turn manager logic
- ✅ Session saving and loading
- ✅ Configuration loading
- ✅ LLM client initialization (mocked)

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

```bash
# Basic test run
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

## Test Structure

```
tests/
├── __init__.py         # Package marker
└── test_basic.py       # All tests in one file (minimalistic)
```

## Adding New Tests

Add new test functions to `test_basic.py`:

```python
def test_your_feature():
    """Test description"""
    # Your test code
    assert expected == actual
```

## Mocking External APIs

The tests mock all external API calls to avoid requiring real API keys:

```python
@patch('anthropic.Anthropic')
def test_with_mocked_api(mock_anthropic):
    mock_anthropic.return_value = MagicMock()
    # Your test code
```