#!/bin/bash

# Run all tests with coverage report
echo "Running all tests with coverage report..."
# Change directory to project root to ensure proper paths
cd "$(dirname "$0")/.." 
python3 -m pytest src/tests/ -v --cov=src --cov-report=term-missing

# Exit with the pytest exit code
exit $? 
