# Tier 2 Integration Tests

This directory contains integration tests for the Tier 2 processor, which uses Ollama with the DeepSeek-R1 model for local LLM processing.

## Test Files

- `test_direct_ollama.py` - Tests direct API calls to Ollama
- `test_ollama_simple.py` - Simple integration test for Ollama client
- `test_ollama_integration.py` - Tests for the OllamaClient integration
- `test_complete_integration.py` - End-to-end test of the full system with Ollama integration

## Requirements

To run these tests, you need:

1. Ollama installed and running (`ollama serve`)
2. DeepSeek-R1 model installed (`ollama pull deepseek-r1-chat-7b-v1.5`)

## Running Tests

You can run all the tests using the provided script:

```bash
./run_tests.sh
```

Or run individual tests:

```bash
python3 test_direct_ollama.py
python3 test_ollama_simple.py
python3 test_ollama_integration.py
python3 test_complete_integration.py
```

## Special Handling for DeepSeek-R1

These tests verify the integration with DeepSeek-R1, which has some special characteristics:

1. Returns NDJSON format responses
2. Uses `<think>...</think>` tags for reasoning
3. Requires special handling for streaming responses

The tests ensure these special cases are handled correctly in our application. 