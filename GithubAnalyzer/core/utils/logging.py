import logging
from typing import Optional

def setup_logger(name: str, log_level: Optional[int] = None) -> logging.Logger:
    """Configure and return a logger instance"""
    logger = logging.getLogger(name)
    if log_level:
        logger.setLevel(log_level)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger 