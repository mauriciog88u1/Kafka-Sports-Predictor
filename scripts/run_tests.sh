"""Test runner script."""
import os
import sys
import pytest

def main():
    """Run the test suite."""
    # Add the project root to the Python path
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)
    
    # Run pytest with coverage
    pytest.main([
        'tests/',  # Run all tests in the tests directory
        '-v',  # Verbose output
        '--cov=src',  # Coverage for src directory
        '--cov-report=term-missing'  # Show missing lines
    ])

if __name__ == '__main__':
    main() 