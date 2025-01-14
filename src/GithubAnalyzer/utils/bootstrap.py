"""Application bootstrap utilities."""

from typing import Any, Dict, Optional, cast

from GithubAnalyzer.config import settings
from GithubAnalyzer.models.core.errors import ConfigError, ServiceError
from GithubAnalyzer.services.core.database_service import DatabaseService
from GithubAnalyzer.utils.container import ServiceContainer
from GithubAnalyzer.utils.logging import setup_logger

logger = setup_logger(__name__)


def init_services(config: Optional[Dict[str, Any]] = None) -> ServiceContainer:
    """Initialize application services.

    Args:
        config: Optional configuration dictionary

    Returns:
        Initialized service container

    Raises:
        ConfigError: If service initialization fails
    """
    try:
        container = ServiceContainer()

        # Register core services
        container.register_service_type("database", DatabaseService)

        # Create services with configuration
        database_config = (
            config.get("database", settings.NEO4J_CONFIG)
            if config
            else settings.NEO4J_CONFIG
        )
        database = cast(
            DatabaseService, container.create_service("database", database_config)
        )

        # Initialize services
        database.initialize()

        return container

    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise ConfigError(f"Service initialization failed: {e}")


def cleanup_services(container: ServiceContainer) -> None:
    """Clean up application services.

    Args:
        container: Service container to clean up
    """
    try:
        if container.has_service("database"):
            database = cast(DatabaseService, container.get_service("database"))
            database.cleanup()
    except Exception as e:
        logger.error(f"Failed to cleanup services: {e}")
