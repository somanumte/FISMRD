
import unittest
import sys
import os

def run_tests():
    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = 'tests'
    suite = loader.discover(start_dir)

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return appropriate exit code
    sys.exit(not result.wasSuccessful())

if __name__ == '__main__':
    run_tests()
