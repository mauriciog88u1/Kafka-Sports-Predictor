#!/usr/bin/env python3
"""Run consumer tests."""
import asyncio
import os
import sys
from dotenv import load_dotenv
import pytest

# Load environment variables
load_dotenv()

def is_running_in_docker():
    """Check if we're running inside a Docker container."""
    return os.path.exists('/.dockerenv')

def main():
    """Run the consumer tests."""
    # Skip container check if running in Docker
    if not is_running_in_docker():
        try:
            # Import here to avoid circular imports
            from scripts.check_containers import check_containers as check
            if not check():
                print("Error: Required containers are not running")
                sys.exit(1)
        except ImportError:
            print("Error: Could not import check_containers script")
            sys.exit(1)
    
    # Run pytest with specific test file
    exit_code = pytest.main([
        "tests/test_consumer.py",
        "-v",  # Verbose output
        "--asyncio-mode=auto",  # Auto-detect async mode
        "-s",  # Show print statements
        "--log-cli-level=INFO"  # Set log level
    ])
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main() 