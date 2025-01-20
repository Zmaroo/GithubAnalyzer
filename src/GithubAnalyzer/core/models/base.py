"""Base model definitions"""

from dataclasses import asdict, dataclass
from typing import Any, Dict


@dataclass
class BaseModel:
    """Base model class for all models in the system."""

    def dict(self) -> Dict[str, Any]:
        """Convert model to dictionary.

        Returns:
            Dictionary representation of the model
        """
        return asdict(self)

    def __str__(self) -> str:
        """Get string representation.

        Returns:
            String representation of the model
        """
        return f"{self.__class__.__name__}({self.dict()})"
