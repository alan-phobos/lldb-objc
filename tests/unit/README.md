# Unit Tests

Pure Python unit tests that require no LLDB runtime.

## Running Tests

```bash
# All unit tests
pytest

# Specific test file
pytest tests/unit/test_objc_utils.py

# Specific test class
pytest tests/unit/test_objc_utils.py::TestParseMethodSignature

# Specific test
pytest tests/unit/test_objc_utils.py::TestParseMethodSignature::test_parse_instance_method

# With verbose output
pytest -v

# With coverage
pytest --cov=scripts --cov-report=html
```

## Test Organization

Tests are organized by source module:

- `test_objc_utils.py` - Tests for `scripts/objc_utils.py` pure functions
- `test_objc_core.py` - Tests for `scripts/objc_core.py` (when created)

## Test Markers

Use markers to categorize and run specific test types:

```bash
# Run only parsing tests
pytest -m parsing

# Run only formatting tests
pytest -m formatting

# Run pattern matching tests
pytest -m pattern
```

Available markers:
- `parsing` - String/regex parsing functions
- `formatting` - Output formatting functions
- `pattern` - Pattern matching and filtering
- `utils` - General utility functions

## Requirements

```bash
pip install pytest pytest-cov
```

## CI/CD

These tests are designed to run in CI on any platform (including Linux),
as they have no LLDB or macOS dependencies.
