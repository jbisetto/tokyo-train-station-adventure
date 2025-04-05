#!/usr/bin/env python
"""
Tokyo Train Station Adventure - Backend Entry Point
"""

import os
import sys
import uvicorn
import logging
import logging.config
from src.api import create_app  # Use absolute import
from src.ai.companion.utils.log_filter import install_sensitive_data_filter

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Define log file path in src directory
log_file_path = os.path.join(current_dir, "backend.log")

# Configure logging
logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": log_file_path,
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5
        }
    },
    "loggers": {
        "src": {
            "level": "DEBUG",
            "handlers": ["console", "file"],
            "propagate": False
        },
        "boto3": {
            "level": "INFO",  # Raise boto3 log level to reduce noise
            "handlers": ["file"],
            "propagate": False
        },
        "botocore": {
            "level": "INFO",  # Raise botocore log level to reduce noise
            "handlers": ["file"],
            "propagate": False
        }
    },
    "root": {
        "level": "DEBUG",
        "handlers": ["console"]
    }
}

# Apply the logging configuration
logging.config.dictConfig(logging_config)

# Install sensitive data filter for all logs
install_sensitive_data_filter()

# Create the FastAPI application
app = create_app()

if __name__ == "__main__":
    # Run the application with uvicorn
    uvicorn.run(
        "src.main:app",  # Use the full module path
        host="0.0.0.0",
        port=8000,
        reload=True,
        factory=False,  # No longer using factory since we create app above
        log_level="debug"
    )
