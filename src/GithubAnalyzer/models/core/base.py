"""Base model definitions and interfaces."""

from typing import Dict


class BaseModel:
    """Base class for all models."""

    def to_dict(self) -> Dict:
        """Convert model to dictionary.

        Returns:
            Dictionary representation of the model.
        """
        return vars(self)

    def from_dict(self, data: Dict) -> None:
        """Update model from dictionary.

        Args:
            data: Dictionary data to update from.
        """
        for key, value in data.items():
            setattr(self, key, value)

    def validate(self) -> None:
        """Validate model state.

        Raises:
            ValueError: If model state is invalid.
        """
        pass
