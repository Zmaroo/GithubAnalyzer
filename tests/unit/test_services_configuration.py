import pytest

from GithubAnalyzer.models.core.errors import ConfigError
from GithubAnalyzer.services.core.configurable import ConfigurableService


def test_service_configuration_initialization():
    """Test service configuration initialization."""
    service = ConfigurableService()
    assert service is not None
    assert hasattr(service, "_config")


def test_service_configuration_validation():
    """Test service configuration validation."""
    service = ConfigurableService()
    with pytest.raises(ConfigError):
        service.validate_config(None)
    with pytest.raises(ConfigError):
        service.validate_config([])

    # Valid config
    config = {"key": "value"}
    validated = service.validate_config(config)
    assert validated == config


def test_service_configuration_update():
    """Test service configuration update."""
    service = ConfigurableService()
    config = {"key": "value"}
    service.update_config(config)
    assert service._config == config


def test_service_configuration_defaults():
    """Test service configuration defaults."""
    service = ConfigurableService()
    assert service._config == {}
    assert service.get_config() == {}
