#!/usr/bin/env python
"""
Top-level entry point to execute the automated scientific benchmark test suite on tests/ and tests_1/.
Usage:
    python test_scripts/run_automated_tests.py                 # Runs both tests/ and tests_1/ suites (default)
    python test_scripts/run_automated_tests.py --dir tests     # Runs only converted tests in tests/
    python test_scripts/run_automated_tests.py --dir tests_1   # Runs sparse tests in tests_1/
    python test_scripts/run_automated_tests.py --fruit banana  # Filter by fruit across suites
"""
import sys
import os
import argparse

# Ensure test_scripts directory and workspace root are in sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from test_runner import run_all_tests

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Eureka Scientific Benchmarks with Automated Preset Calibration")
    parser.add_argument("--fruit", type=str, default=None, help="Filter by fruit name")
    parser.add_argument("--dir", type=str, default="all", help="Target test directory ('tests', 'tests_1', or 'all' to run both, default: all)")
    parser.add_argument("--no-optimize", action="store_true", help="Skip automated preset calibration analysis")
    args = parser.parse_args()
    
    run_all_tests(
        fruit_filter=args.fruit,
        test_dir=args.dir,
        auto_optimize=not args.no_optimize
    )
