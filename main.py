import logging.config
from src.GithubAnalyzer.core.utils.logging import configure_logging

def main():
    # Configure logging
    configure_logging()

    # Your application code here
    print("Application started")

if __name__ == "__main__":
    main()