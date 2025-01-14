"""Pattern detection and analysis utilities."""

from pathlib import Path
from typing import Dict, List, Set

from ...models.analysis.patterns import FRAMEWORK_PATTERNS, PATTERN_CATEGORIES, Pattern
from ...utils.logging import setup_logger

logger = setup_logger(__name__)


class PatternDetector:
    """Detects code patterns and usage patterns."""

    @staticmethod
    def detect_all(parse_result: Dict, file_path: str) -> Dict[str, List[str]]:
        """Detect all patterns in code.

        Args:
            parse_result: Parsed code result.
            file_path: Path to the file being analyzed.

        Returns:
            Dictionary of detected patterns by category.
        """
        patterns = {category: [] for category in PATTERN_CATEGORIES}

        try:
            # Detect framework patterns
            if framework_patterns := PatternDetector.detect_framework_patterns(
                Path(file_path)
            ):
                patterns["framework"].extend(framework_patterns)

            # Add other pattern detection methods here
            # ...

        except Exception as e:
            logger.error(f"Error detecting patterns: {e}")

        return patterns

    @staticmethod
    def detect_framework_patterns(file_path: Path) -> List[str]:
        """Detect framework usage patterns.

        Args:
            file_path: Path to the file being analyzed.

        Returns:
            List of detected framework patterns.
        """
        detected = []
        try:
            for framework, patterns in FRAMEWORK_PATTERNS.items():
                if file_path.name in patterns:
                    detected.append(framework)
        except Exception as e:
            logger.error(f"Error detecting framework patterns: {e}")
        return detected
