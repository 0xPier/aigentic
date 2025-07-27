"""
Test runner script for the AI consultancy platform.
Provides comprehensive test execution with coverage reporting and performance metrics.
"""

import pytest
import sys
import os
import time
from pathlib import Path
import subprocess
import argparse
from typing import List, Dict, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestRunner:
    """Comprehensive test runner with reporting and metrics."""
    
    def __init__(self):
        self.test_dir = Path(__file__).parent
        self.project_root = self.test_dir.parent
        self.coverage_threshold = 80  # Minimum coverage percentage
        
    def run_all_tests(self, verbose: bool = True, coverage: bool = True) -> Dict[str, Any]:
        """Run all tests with optional coverage reporting."""
        print("🚀 Starting comprehensive test suite for AI Consultancy Platform")
        print("=" * 70)
        
        start_time = time.time()
        results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "coverage": 0,
            "duration": 0,
            "test_categories": {}
        }
        
        # Test categories to run
        test_categories = [
            ("Agent Tests", "test_agents/"),
            ("API Tests", "test_api/"),
            ("Integration Tests", "test_integration/") if (self.test_dir / "test_integration").exists() else None
        ]
        
        test_categories = [cat for cat in test_categories if cat is not None]
        
        for category_name, test_path in test_categories:
            print(f"\n📋 Running {category_name}")
            print("-" * 50)
            
            category_results = self._run_test_category(test_path, verbose)
            results["test_categories"][category_name] = category_results
            
            # Aggregate results
            results["total_tests"] += category_results.get("total", 0)
            results["passed"] += category_results.get("passed", 0)
            results["failed"] += category_results.get("failed", 0)
            results["skipped"] += category_results.get("skipped", 0)
        
        # Run coverage if requested
        if coverage:
            print(f"\n📊 Generating coverage report")
            print("-" * 50)
            coverage_result = self._run_coverage_analysis()
            results["coverage"] = coverage_result
        
        results["duration"] = time.time() - start_time
        
        # Print summary
        self._print_test_summary(results)
        
        return results
    
    def _run_test_category(self, test_path: str, verbose: bool = True) -> Dict[str, Any]:
        """Run tests for a specific category."""
        full_path = self.test_dir / test_path
        
        if not full_path.exists():
            print(f"⚠️  Test directory {test_path} not found, skipping...")
            return {"total": 0, "passed": 0, "failed": 0, "skipped": 0}
        
        # Build pytest command
        cmd = [
            sys.executable, "-m", "pytest",
            str(full_path),
            "-v" if verbose else "-q",
            "--tb=short",
            "--disable-warnings",
            "--color=yes"
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.project_root)
            )
            
            # Parse pytest output for statistics
            output_lines = result.stdout.split('\n')
            stats = self._parse_pytest_output(output_lines)
            
            if result.returncode == 0:
                print(f"✅ All tests passed in {test_path}")
            else:
                print(f"❌ Some tests failed in {test_path}")
                if verbose:
                    print("Error output:")
                    print(result.stderr)
            
            return stats
            
        except Exception as e:
            print(f"❌ Error running tests in {test_path}: {str(e)}")
            return {"total": 0, "passed": 0, "failed": 0, "skipped": 0, "error": str(e)}
    
    def _parse_pytest_output(self, output_lines: List[str]) -> Dict[str, Any]:
        """Parse pytest output to extract test statistics."""
        stats = {"total": 0, "passed": 0, "failed": 0, "skipped": 0}
        
        for line in output_lines:
            if "passed" in line and "failed" in line:
                # Look for summary line like "5 failed, 10 passed in 2.34s"
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == "passed" and i > 0:
                        try:
                            stats["passed"] = int(parts[i-1])
                        except (ValueError, IndexError):
                            pass
                    elif part == "failed" and i > 0:
                        try:
                            stats["failed"] = int(parts[i-1])
                        except (ValueError, IndexError):
                            pass
                    elif part == "skipped" and i > 0:
                        try:
                            stats["skipped"] = int(parts[i-1])
                        except (ValueError, IndexError):
                            pass
            elif "passed in" in line:
                # Look for simple passed line like "10 passed in 2.34s"
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == "passed" and i > 0:
                        try:
                            stats["passed"] = int(parts[i-1])
                        except (ValueError, IndexError):
                            pass
        
        stats["total"] = stats["passed"] + stats["failed"] + stats["skipped"]
        return stats
    
    def _run_coverage_analysis(self) -> Dict[str, Any]:
        """Run coverage analysis on the test suite."""
        try:
            # Install coverage if not available
            subprocess.run([sys.executable, "-m", "pip", "install", "coverage"], 
                         capture_output=True, check=False)
            
            # Run tests with coverage
            cmd = [
                sys.executable, "-m", "coverage", "run",
                "--source=src",
                "-m", "pytest",
                str(self.test_dir),
                "-q"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.project_root)
            )
            
            # Generate coverage report
            report_cmd = [sys.executable, "-m", "coverage", "report", "--format=text"]
            report_result = subprocess.run(
                report_cmd,
                capture_output=True,
                text=True,
                cwd=str(self.project_root)
            )
            
            # Parse coverage percentage
            coverage_pct = self._parse_coverage_output(report_result.stdout)
            
            # Generate HTML report
            html_cmd = [sys.executable, "-m", "coverage", "html", "--directory=htmlcov"]
            subprocess.run(html_cmd, capture_output=True, cwd=str(self.project_root))
            
            return {
                "percentage": coverage_pct,
                "report": report_result.stdout,
                "html_report": "htmlcov/index.html"
            }
            
        except Exception as e:
            print(f"⚠️  Coverage analysis failed: {str(e)}")
            return {"percentage": 0, "error": str(e)}
    
    def _parse_coverage_output(self, coverage_output: str) -> float:
        """Parse coverage output to extract percentage."""
        lines = coverage_output.split('\n')
        for line in lines:
            if "TOTAL" in line and "%" in line:
                parts = line.split()
                for part in parts:
                    if part.endswith('%'):
                        try:
                            return float(part[:-1])
                        except ValueError:
                            pass
        return 0.0
    
    def _print_test_summary(self, results: Dict[str, Any]):
        """Print comprehensive test summary."""
        print("\n" + "=" * 70)
        print("🎯 TEST EXECUTION SUMMARY")
        print("=" * 70)
        
        # Overall statistics
        total = results["total_tests"]
        passed = results["passed"]
        failed = results["failed"]
        skipped = results["skipped"]
        duration = results["duration"]
        
        print(f"📊 Overall Results:")
        print(f"   Total Tests: {total}")
        print(f"   ✅ Passed: {passed}")
        print(f"   ❌ Failed: {failed}")
        print(f"   ⏭️  Skipped: {skipped}")
        print(f"   ⏱️  Duration: {duration:.2f}s")
        
        if total > 0:
            success_rate = (passed / total) * 100
            print(f"   📈 Success Rate: {success_rate:.1f}%")
        
        # Category breakdown
        if results["test_categories"]:
            print(f"\n📋 Category Breakdown:")
            for category, stats in results["test_categories"].items():
                if stats.get("total", 0) > 0:
                    cat_success = (stats["passed"] / stats["total"]) * 100
                    print(f"   {category}: {stats['passed']}/{stats['total']} ({cat_success:.1f}%)")
        
        # Coverage information
        if results.get("coverage"):
            coverage_pct = results["coverage"].get("percentage", 0)
            print(f"\n📊 Code Coverage: {coverage_pct:.1f}%")
            
            if coverage_pct >= self.coverage_threshold:
                print(f"   ✅ Coverage meets threshold ({self.coverage_threshold}%)")
            else:
                print(f"   ⚠️  Coverage below threshold ({self.coverage_threshold}%)")
            
            if "html_report" in results["coverage"]:
                print(f"   📄 HTML Report: {results['coverage']['html_report']}")
        
        # Final status
        print("\n" + "=" * 70)
        if failed == 0 and total > 0:
            print("🎉 ALL TESTS PASSED! Platform is ready for deployment.")
        elif failed > 0:
            print(f"⚠️  {failed} TESTS FAILED. Please review and fix issues.")
        else:
            print("⚠️  No tests were executed. Please check test configuration.")
        print("=" * 70)
    
    def run_specific_tests(self, test_pattern: str, verbose: bool = True) -> Dict[str, Any]:
        """Run specific tests matching a pattern."""
        print(f"🎯 Running tests matching pattern: {test_pattern}")
        print("-" * 50)
        
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.test_dir),
            "-k", test_pattern,
            "-v" if verbose else "-q",
            "--tb=short",
            "--disable-warnings",
            "--color=yes"
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.project_root)
            )
            
            output_lines = result.stdout.split('\n')
            stats = self._parse_pytest_output(output_lines)
            
            print(f"Results: {stats['passed']} passed, {stats['failed']} failed")
            
            if result.returncode != 0 and verbose:
                print("Error output:")
                print(result.stderr)
            
            return stats
            
        except Exception as e:
            print(f"❌ Error running specific tests: {str(e)}")
            return {"error": str(e)}
    
    def run_performance_tests(self) -> Dict[str, Any]:
        """Run performance-focused tests."""
        print("⚡ Running performance tests")
        print("-" * 50)
        
        # Look for performance test markers
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.test_dir),
            "-m", "performance",
            "-v",
            "--tb=short",
            "--disable-warnings"
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.project_root)
            )
            
            if "no tests ran" in result.stdout.lower():
                print("ℹ️  No performance tests found (use @pytest.mark.performance)")
                return {"message": "No performance tests found"}
            
            output_lines = result.stdout.split('\n')
            stats = self._parse_pytest_output(output_lines)
            
            print(f"Performance test results: {stats}")
            return stats
            
        except Exception as e:
            print(f"❌ Error running performance tests: {str(e)}")
            return {"error": str(e)}


def main():
    """Main entry point for test runner."""
    parser = argparse.ArgumentParser(description="AI Consultancy Platform Test Runner")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage analysis")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--pattern", "-k", help="Run tests matching pattern")
    parser.add_argument("--performance", action="store_true", help="Run performance tests only")
    parser.add_argument("--quick", "-q", action="store_true", help="Quick run without coverage")
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    try:
        if args.performance:
            results = runner.run_performance_tests()
        elif args.pattern:
            results = runner.run_specific_tests(args.pattern, args.verbose)
        else:
            coverage = args.coverage and not args.quick
            results = runner.run_all_tests(args.verbose, coverage)
        
        # Exit with appropriate code
        if results.get("failed", 0) > 0:
            sys.exit(1)
        elif results.get("error"):
            sys.exit(2)
        else:
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\n⚠️  Test execution interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        sys.exit(3)


if __name__ == "__main__":
    main()
