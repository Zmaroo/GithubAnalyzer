"""Pattern definitions and configurations."""

from typing import Dict, List, Optional

# Framework detection patterns
FRAMEWORK_PATTERNS: Dict[str, List[str]] = {
    "django": [
        "manage.py",
        "wsgi.py",
        "asgi.py",
        "settings.py",
        "urls.py",
        "**/models/__init__.py",  # Django models directory
        "**/views/__init__.py",   # Django views directory
        "admin.py",
    ],
    "flask": ["app.py", "wsgi.py", "config.py", "requirements.txt"],
    "fastapi": ["main.py", "app.py", "api.py", "requirements.txt"],
}

# Code pattern categories
PATTERN_CATEGORIES = {
    "usage": "Patterns related to API and library usage",
    "framework": "Framework-specific patterns",
    "style": "Code style and convention patterns",
    "architectural": "Software architecture patterns",
}


class Pattern:
    """Base class for code patterns."""

    def __init__(self, name: str, category: str, description: Optional[str] = None):
        """Initialize a pattern.

        Args:
            name: Pattern name
            category: Pattern category
            description: Optional pattern description
        """
        self.name = name
        self.category = category
        self.description = description or ""

    def matches(self, ast: Dict) -> bool:
        """Check if pattern matches AST.

        Args:
            ast: Abstract syntax tree to check

        Returns:
            True if pattern matches, False otherwise
        """
        raise NotImplementedError
