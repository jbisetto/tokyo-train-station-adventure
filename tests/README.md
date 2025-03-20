# Tokyo Train Station Adventure Tests

This directory contains all tests for the Tokyo Train Station Adventure project.

## Test Structure

The tests are organized by module and test type:

- `backend/` - Tests for backend code
  - `ai/` - AI companion tests
    - `companion/` - Tests for the companion AI modules
      - `core/` - Core module tests
      - `tier1/` - Tier 1 (rules-based) processor tests
      - `tier2/` - Tier 2 (local LLM) processor tests
      - `tier3/` - Tier 3 (cloud LLM) processor tests
      - `integration/` - Tests that integrate multiple components
  - `api/` - API endpoint tests
  - `integration/` - Integration tests
    - `tier2/` - Tier 2 integration tests (Ollama, DeepSeek-R1)
    - `tier3/` - Tier 3 integration tests (AWS Bedrock)

## Running Tests

You can run tests in several ways:

### Run All Tests

```bash
# Run all tests
./run_all_tests.sh
```

### Run Specific Test Groups

```bash
# Run unit tests for a specific module
python -m pytest backend/ai/companion/core -v

# Run tier1 tests
python -m pytest backend/ai/companion/tier1 -v

# Run tier2 tests
python -m pytest backend/ai/companion/tier2 -v

# Run tier3 tests
python -m pytest backend/ai/companion/tier3 -v

# Run API tests
python -m pytest backend/api -v
```

### Run Integration Tests

```bash
# Run tier2 integration tests (Ollama)
cd backend/integration/tier2
./run_tests.sh

# Run tier3 integration tests (Bedrock)
python -m pytest backend/integration/tier3 -v
```

## Test Requirements

### Tier 2 Integration Tests

The Tier 2 integration tests require:
- Ollama installed and running (`ollama serve`)
- DeepSeek-R1 model installed (`ollama pull deepseek-r1-chat-7b-v1.5`)

### Tier 3 Integration Tests

The Tier 3 integration tests require:
- AWS credentials configured
- Access to AWS Bedrock models
