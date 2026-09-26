#!/usr/bin/env python3
"""
Test runner for Incisive Nova data contracts.
"""

import sys
import os
import pytest

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def run_tests():
    """Run all schema tests."""
    test_dir = os.path.join(os.path.dirname(__file__), 'schemas')
    
    print("=" * 80)
    print("Running Incisive Nova Data Contract Tests")
    print("=" * 80)
    print()
    
    # Run tests with verbose output
    result = pytest.main([
        test_dir,
        "-v",  # Verbose output
        "--tb=short",  # Short traceback
        "--maxfail=5",  # Stop after 5 failures
    ])
    
    print()
    print("=" * 80)
    if result == 0:
        print("✅ All tests passed!")
    else:
        print(f"❌ Tests failed with exit code: {result}")
    print("=" * 80)
    
    return result

if __name__ == "__main__":
    sys.exit(run_tests())