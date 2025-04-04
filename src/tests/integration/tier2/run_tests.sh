#!/bin/bash
# Tier 2 Integration Tests Runner

# Set Python path to include the repository root
export PYTHONPATH="${PYTHONPATH}:$(cd ../../../../ && pwd)"
echo "PYTHONPATH set to: $PYTHONPATH"

# Change to the script directory
cd "$(dirname "$0")"

# Check if Ollama is running
echo "Checking if Ollama service is running..."
if ! curl -s "http://localhost:11434/api/version" > /dev/null; then
    echo "❌ ERROR: Ollama service is not running. Please start it with 'ollama serve'."
    exit 1
else
    echo "✅ Ollama service is running."
fi

# Run the direct API test
echo "Running direct Ollama API test..."
python3 test_direct_ollama.py
echo ""

# Run the simple integration test
echo "Running simple Ollama integration test..."
python3 test_ollama_simple.py
echo ""

# Run the OllamaClient integration test
echo "Running OllamaClient integration test..."
python3 test_ollama_integration.py
echo ""

# Run the complete system integration test
echo "Running complete system integration test..."
python3 test_complete_integration.py
echo ""

echo "All tests completed." 