#!/bin/bash

# Run all tests with coverage report
echo "Running all tests with coverage report..."
python3 -m pytest tests/ -v --cov=src --cov-report=term-missing

# Exit with the pytest exit code
exit $? 
