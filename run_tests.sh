#!/bin/bash

# Run all tests with coverage report
echo "Running all tests with coverage report..."
python3 -m pytest tests/ -v --cov=backend --cov-report=term-missing

# Exit with the pytest exit code
exit $? 
