"""Test runner for GithubAnalyzer"""
import pytest
import sys
from pathlib import Path
import logging

def setup_test_logging():
    """Configure logging for tests"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('tests/test.log')
        ]
    )

def run_tests():
    """Run all tests in order"""
    setup_test_logging()
    logger = logging.getLogger(__name__)
    
    test_suites = [
        # Core components
        "test_parsers/test_tree_sitter.py",
        "test_parsers/test_custom_parsers.py",
        
        # Services
        "test_services/test_graph_analysis_service.py",
        "test_services/test_combined_analysis.py",
        "test_services/test_analyzer_service.py",
        "test_services/test_parser_service.py",
        "test_services/test_database_service.py",
        "test_services/test_framework_service.py",
        
        # Integration tests
        "test_services/test_service_integration.py",
        "test_services/test_service_integration_complex.py",
        
        # Performance tests
        "test_services/test_service_performance.py",
        
        # Security tests
        "test_services/test_service_security.py"
    ]
    
    failed_tests = []
    
    for test_suite in test_suites:
        logger.info(f"Running test suite: {test_suite}")
        result = pytest.main([
            f"tests/{test_suite}",
            "-v",
            "--tb=short",
            "--show-capture=no"
        ])
        
        if result != pytest.ExitCode.OK:
            failed_tests.append(test_suite)
    
    if failed_tests:
        logger.error("The following test suites failed:")
        for test in failed_tests:
            logger.error(f"  - {test}")
        sys.exit(1)
    else:
        logger.info("All test suites passed successfully!")

if __name__ == "__main__":
    run_tests() 