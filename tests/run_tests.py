"""
Test runner for the reminder service unittest suite
Runs all unittest test cases and provides a summary
"""

import unittest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_all_tests():
    """Run all unittest test cases"""
    # Discover and run all tests
    loader = unittest.TestLoader()
    suite = loader.discover('tests', pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return True if all tests passed
    return result.wasSuccessful()


def run_specific_test(test_file):
    """Run a specific test file"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName(f'tests.{test_file}')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        # Run specific test file
        test_file = sys.argv[1].replace('.py', '')
        success = run_specific_test(test_file)
    else:
        # Run all tests
        success = run_all_tests()
    
    sys.exit(0 if success else 1)