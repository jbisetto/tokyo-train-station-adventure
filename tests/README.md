# Tokyo Train Station Adventure 
## Testing

The project follows a Test-Driven Development (TDD) approach, with comprehensive test coverage for all components. The tests are organized to match the module structure of the codebase.

### Setting Up the Test Environment

1. Create and activate a virtual environment:
   ```bash
   python -m venv tokyo-py
   source tokyo-py/bin/activate  # On Windows: tokyo-py\Scripts\activate
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

   Alternatively, you can install the testing dependencies directly:
   ```bash
   pip install pytest pytest-asyncio pytest-cov pytest-mock pyyaml aiohttp boto3
   ```

### Running Tests

- Run all tests:
  ```bash
  python -m pytest
  ```

- Run tests for a specific module:
  ```bash
  python -m pytest tests/backend/ai/companion/tier3/
  ```

- Run a specific test file:
  ```bash
  python -m pytest tests/backend/ai/companion/tier3/test_tier3_processor.py
  ```

- Run a specific test:
  ```bash
  python -m pytest tests/backend/ai/companion/tier3/test_tier3_processor.py::TestTier3Processor::test_process
  ```

- Run tests with verbose output:
  ```bash
  python -m pytest -v
  ```

- Run tests with coverage report:
  ```bash
  python -m pytest --cov=backend
  ```

### Test Structure

The test suite is organized to mirror the structure of the codebase:

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test interactions between components
- **Functional Tests**: Test complete workflows

Each module in the companion AI system has corresponding test files that verify its functionality:

```
tests/
└── backend/
    └── ai/
        └── companion/
            ├── core/              # Tests for core components
            ├── tier1/             # Tests for rule-based processing
            ├── tier2/             # Tests for local LLM integration
            ├── tier3/             # Tests for cloud API integration
            └── utils/             # Tests for utility functions
```

### Continuous Integration

The project uses a shell script to run all tests as part of the development workflow:

```bash
./run_tests.sh
```

This script runs the full test suite and generates a coverage report.
