#!/bin/bash

# Run pytest with coverage report
python3 -m pytest tests/ -v --cov=backend --cov-report=term-missing 
