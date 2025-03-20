# Tier 2 (Ollama) Integration Tests

This directory contains integration tests for the Tier 2 processor, which uses Ollama to run local language models like DeepSeek-R1.

## Test Files

1. **test_ollama_simple.py**: A simple standalone test to verify basic connectivity and response processing with Ollama.

2. **test_direct_ollama.py**: Direct test of the Ollama API without involving application code.

3. **test_ollama_integration.py**: An integration test for the OllamaClient class specifically.

4. **test_complete_integration.py**: A complete integration test that processes a request through the entire system pipeline.

## Running the Tests

You can run the tests using the provided shell script:

```bash
./run_tests.sh
```

Or run individual tests:

```bash
python3 test_ollama_simple.py
python3 test_complete_integration.py
```

## Requirements

- Ollama must be running locally (`ollama serve`)
- The DeepSeek-R1 model must be installed (`ollama pull deepseek-r1:latest`)
- The Tier 2 processor must be enabled in the configuration

## Notes on DeepSeek-R1 Model

The DeepSeek-R1 model has a few specific characteristics:

1. It returns responses in a streaming ndjson format, even when `stream: false` is specified
2. It includes thinking tags `<think>...</think>` which need to be filtered out
3. For more details on handling DeepSeek-R1 responses, see the README-DEEPSEEK-OLLAMA.md file in the repository root 