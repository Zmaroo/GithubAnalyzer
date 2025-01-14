"""Common test fixtures and utilities"""

from typing import Any, Dict, Optional, Type, TypeVar

import pytest
from pytest import FixtureRequest

from GithubAnalyzer.models.core.config.settings import settings
from GithubAnalyzer.services.core.base_service import BaseService
from GithubAnalyzer.services.core.dependency_container import DependencyContainer

T = TypeVar("T", bound=BaseService)


@pytest.fixture(scope="session")
def container() -> DependencyContainer:
    """Get the dependency container instance"""
    return DependencyContainer.get_instance()


@pytest.fixture(scope="session")
def test_config() -> Dict[str, Any]:
    """Get test configuration"""
    return {
        "database": {
            "host": "localhost",
            "port": 5432,
            "database": "test_db",
            "user": "test_user",
            "password": "test_pass",
            "enable_ssl": False,
            "connection_pooling": False,
        },
        "parser": {"max_file_size": 1048576, "require_type_hints": True},
        "analyzer": {"enable_security_checks": True, "enable_type_checking": True},
        "graph": {"check_gds_patterns": True, "validate_projections": True},
        "framework": {"enable_validation": True, "enable_caching": True},
    }


class BaseServiceTest:
    """Base class for service tests"""

    @pytest.fixture
    def container(self, container: DependencyContainer) -> DependencyContainer:
        """Get container instance"""
        return container

    @pytest.fixture
    def config(self, test_config: Dict[str, Any]) -> Dict[str, Any]:
        """Get test configuration"""
        return test_config

    def get_service(self, container: DependencyContainer, name: str) -> Optional[T]:
        """Get a service from the container"""
        return container.get_service(name)
