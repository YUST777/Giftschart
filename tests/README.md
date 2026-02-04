# GiftsChart Tests

This directory contains all tests for the GiftsChart bot.

## Running Tests

### Run all tests
```bash
pytest tests/ -v
```

### Run specific test file
```bash
pytest tests/test_gift_cards.py -v
```

### Run with coverage
```bash
pytest tests/ --cov=. --cov-report=html
```

### Run specific test class
```bash
pytest tests/test_gift_cards.py::TestGiftCardGeneration -v
```

### Run specific test method
```bash
pytest tests/test_gift_cards.py::TestGiftCardGeneration::test_gift_card_template_exists -v
```

## Test Structure

```
tests/
├── __init__.py                    # Test package initialization
├── test_gift_cards.py             # Gift card functionality tests
├── test_sticker_integration.py    # Sticker functionality tests
├── test_rate_limiter.py           # Rate limiting tests
└── README.md                      # This file
```

## Writing Tests

### Test Naming Convention
- Test files: `test_*.py`
- Test classes: `Test*`
- Test methods: `test_*`

### Example Test
```python
import pytest

class TestMyFeature:
    """Test my feature functionality."""
    
    def test_something(self):
        """Test that something works."""
        result = my_function()
        assert result == expected_value
```

### Using Fixtures
```python
@pytest.fixture
def sample_data():
    """Provide sample data for tests."""
    return {"key": "value"}

def test_with_fixture(sample_data):
    """Test using fixture data."""
    assert sample_data["key"] == "value"
```

## Test Coverage

Current test coverage focuses on:
- ✅ Gift card generation
- ✅ Sticker integration
- ✅ Rate limiting logic
- 🚧 Premium system (TODO)
- 🚧 API integrations (TODO)
- 🚧 Database operations (TODO)

## CI/CD Integration

Tests are automatically run on:
- Every push to `main` and `develop` branches
- Every pull request
- Python versions: 3.10, 3.11, 3.12

See `.github/workflows/python-tests.yml` for CI configuration.

## Test Requirements

Install test dependencies:
```bash
pip install pytest pytest-cov flake8 mypy
```

## Best Practices

1. **Write descriptive test names** - Test names should clearly describe what is being tested
2. **One assertion per test** - Keep tests focused and simple
3. **Use fixtures** - Reuse common test data and setup
4. **Test edge cases** - Don't just test the happy path
5. **Keep tests fast** - Avoid slow operations when possible
6. **Mock external dependencies** - Don't rely on external APIs in tests

## TODO

- [ ] Add tests for premium system
- [ ] Add tests for API integrations
- [ ] Add tests for database operations
- [ ] Add integration tests
- [ ] Add end-to-end tests
- [ ] Increase test coverage to 80%+
