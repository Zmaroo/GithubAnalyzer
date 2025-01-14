"""Test dependency injection functionality."""

from GithubAnalyzer.services.core.dependency_container import DependencyContainer


def test_di_metadata() -> None:
    """Test dependency injection metadata handling."""
    container = DependencyContainer()

    # pylint: disable=protected-access
    # Access to protected members is needed for testing
    metadata = container._metadata
    assert isinstance(metadata, dict)


def test_di_services() -> None:
    """Test service registration and retrieval."""
    container = DependencyContainer()

    # pylint: disable=protected-access
    services = container._services
    registry = container._registry
    assert isinstance(services, dict)
    assert isinstance(registry, dict)
