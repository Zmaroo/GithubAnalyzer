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
            logging.FileHandler('test.log')
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
        "test_parsers/conftest.py",
        "test_code_parser.py",
        
        # Services
        "test_services/test_graph_analysis_service.py",
        "test_services/test_analyzer_service.py",
        "test_services/test_parser_service.py",
        "test_services/test_database_service.py",
        
        # CLI Tests
        "test_ai_agent_cli.py",
        
        # Integration tests
        "test_services/test_service_integration.py",
    ]
    
    failed_tests = []
    test_dir = Path(__file__).parent
    
    for test_suite in test_suites:
        test_path = test_dir / test_suite
        if not test_path.exists():
            logger.warning(f"Test suite not found: {test_suite}")
            continue
            
        logger.info(f"Running test suite: {test_suite}")
        result = pytest.main([
            str(test_path),
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