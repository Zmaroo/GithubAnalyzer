"""Database utility functions."""


def get_connection_string(host: str, port: int, database: str) -> str:
    """Generate database connection string.

    Args:
        host: Database host.
        port: Database port.
        database: Database name.

    Returns:
        Connection string.
    """
    return f"postgresql://{host}:{port}/{database}"
