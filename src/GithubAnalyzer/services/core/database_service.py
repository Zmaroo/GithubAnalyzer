"""Database service implementation."""

from typing import Dict, Optional

from ...models.core.errors import ConfigError, ServiceError
from ...models.storage.database import DatabaseConfig, DatabaseConnection
from .base_service import ConfigurableService


class DatabaseService(ConfigurableService):
    """Service for managing database operations."""

    def __init__(self, config: Optional[Dict[str, str]] = None) -> None:
        """Initialize database service.

        Args:
            config: Optional database configuration.
        """
        default_config = {
            "host": "localhost",
            "port": "5432",
            "database": "github_analyzer",
            "username": "postgres",
            "password": "postgres",
            "max_connections": "10",
            "timeout": "30",
            "ssl_enabled": "false",
            "retry_attempts": "3",
        }
        if config:
            default_config.update(config)
        super().__init__(default_config)
        self._connection: Optional[DatabaseConnection] = None

    def _validate_config(self) -> None:
        """Validate database configuration.

        Raises:
            ConfigError: If configuration is invalid.
        """
        required_keys = ["host", "port", "database", "username", "password"]
        for key in required_keys:
            if key not in self._config:
                raise ConfigError(f"Missing required configuration key: {key}")

    def _start_impl(self) -> None:
        """Start database service.

        Raises:
            ServiceError: If service fails to start.
        """
        try:
            config = DatabaseConfig(
                host=self._config["host"],
                port=int(self._config["port"]),
                database=self._config["database"],
                username=self._config["username"],
                password=self._config["password"],
                max_connections=int(self._config.get("max_connections", "10")),
                timeout=int(self._config.get("timeout", "30")),
                ssl_enabled=self._config.get("ssl_enabled", "false").lower() == "true",
                retry_attempts=int(self._config.get("retry_attempts", "3")),
            )
            self._connection = DatabaseConnection(config)
            self._connection.connect()
        except Exception as e:
            raise ServiceError(f"Failed to start database service: {e}") from e

    def _stop_impl(self) -> None:
        """Stop database service.

        Raises:
            ServiceError: If service fails to stop.
        """
        try:
            if self._connection:
                self._connection.close()
                self._connection = None
        except Exception as e:
            raise ServiceError(f"Failed to stop database service: {e}") from e

    def get_connection(self) -> DatabaseConnection:
        """Get database connection.

        Returns:
            DatabaseConnection: Active database connection.

        Raises:
            ServiceError: If no active connection exists.
        """
        if not self._connection:
            raise ServiceError("No active database connection")
        return self._connection

    def execute_query(self, query: str) -> Dict:
        """Execute database query.

        Args:
            query: SQL query to execute.

        Returns:
            Dict: Query results.

        Raises:
            ServiceError: If query execution fails.
        """
        try:
            conn = self.get_connection()
            return conn.execute(query)
        except Exception as e:
            raise ServiceError(f"Failed to execute query: {e}") from e
