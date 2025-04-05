# Test Reorganization Plan

## Current Structure
- `tests/` - Main test directory (organized by module)
- `backend/tests/` - Backend integration tests for Tier2/Ollama
- Project root - Three test files: `test_bedrock.py`, `test_ollama_integration.py`, `test_ollama_simple.py`

## Target Structure
All tests should be consolidated in the `tests/` directory while preserving the organizational structure.

## Changes Needed

1. Create directory for integration tests:
```bash
mkdir -p tests/backend/integration/tier2
```

2. Move integration tests from `backend/tests/integration/tier2/` to `tests/backend/integration/tier2/`:
```bash
cp backend/tests/integration/tier2/test_*.py tests/backend/integration/tier2/
cp backend/tests/integration/tier2/run_tests.sh tests/backend/integration/tier2/
```

3. Move root level test files to appropriate locations:
```bash
# Move Ollama integration tests to the tier2 integration tests folder
cp test_ollama_integration.py tests/backend/integration/tier2/
cp test_ollama_simple.py tests/backend/integration/tier2/

# Move Bedrock test to the tier3 integration tests folder
mkdir -p tests/backend/integration/tier3
cp test_bedrock.py tests/backend/integration/tier3/
```

4. Update imports and paths in the moved files if necessary

5. Update the run_tests.sh script to reflect the new paths

6. Create a main run_tests.sh in the tests directory to run all tests

7. Once verified working, we can remove the original files from the root and backend/tests directories

## Testing Approach
After moving each set of files, run the tests to ensure they still work correctly before removing the original files. 