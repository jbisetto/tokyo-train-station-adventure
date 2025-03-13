#!/usr/bin/env python
"""
Simple server runner for Tokyo Train Station Adventure.
"""

import os
import sys
import uvicorn

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "backend.api:create_app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        factory=True
    ) 