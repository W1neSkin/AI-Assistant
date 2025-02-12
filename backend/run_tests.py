#!/usr/bin/env python
import argparse
import subprocess
import sys
import os
from typing import List

class TestRunner:
    def __init__(self):
        self.test_dir = "tests"
        self.coverage_dir = "coverage"
        
    def run_tests(self, test_type: str = "all", coverage: bool = False, verbose: bool = False) -> int:
        """Run specified tests with given options"""
        command = self._build_command(test_type, coverage, verbose)
        return subprocess.run(command, shell=True).returncode
    
    def _build_command(self, test_type: str, coverage: bool, verbose: bool) -> str:
        """Build pytest command with appropriate options"""
        cmd_parts: List[str] = ["pytest"]
        
        # Add coverage options
        if coverage:
            cmd_parts.extend([
                "--cov=app",
                "--cov-report=term-missing",
                f"--cov-report=html:{self.coverage_dir}",
                "--cov-branch"
            ])
        
        # Add verbosity
        if verbose:
            cmd_parts.append("-vv")
            
        # Add test selection
        if test_type == "unit":
            cmd_parts.append("tests/unit/")
        elif test_type == "integration":
            cmd_parts.append("tests/integration/")
        else:
            cmd_parts.append("tests/")
            
        return " ".join(cmd_parts)
    
    def clean(self):
        """Clean up test artifacts"""
        # Remove coverage data
        subprocess.run("rm -rf .coverage", shell=True)
        subprocess.run(f"rm -rf {self.coverage_dir}", shell=True)
        # Remove pytest cache
        subprocess.run("rm -rf .pytest_cache", shell=True)
        # Remove pycache
        subprocess.run("find . -type d -name __pycache__ -exec rm -r {} +", shell=True)

def main():
    parser = argparse.ArgumentParser(description="Run tests for the AI Assistant API")
    parser.add_argument(
        "--type",
        choices=["all", "unit", "integration"],
        default="all",
        help="Type of tests to run"
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Generate coverage report"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean test artifacts before running"
    )
    
    args = parser.parse_args()
    
    # Set up environment for tests
    os.environ["TESTING"] = "true"
    
    runner = TestRunner()
    
    if args.clean:
        runner.clean()
    
    try:
        result = runner.run_tests(args.type, args.coverage, args.verbose)
        sys.exit(result)
    except KeyboardInterrupt:
        print("\nTest run interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError running tests: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 