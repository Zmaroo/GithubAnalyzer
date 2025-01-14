"""Repository manager service."""

import logging
import os
from typing import Any, Dict, List, Optional

from git import Repo

from ...models.core.errors import ServiceError
from ...models.core.repository import RepositoryInfo
from .base_service import BaseService


class RepositoryManager(BaseService):
    """Service for managing code repositories."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the repository manager.

        Args:
            config: Optional configuration dictionary
        """
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        self._repo = None
        self._initialized = False

    def initialize(self) -> None:
        """Initialize the repository manager.

        Raises:
            ServiceError: If initialization fails
        """
        try:
            self._initialized = True
            self.logger.info("Repository manager initialized successfully")
        except Exception as e:
            self.logger.error("Failed to initialize repository manager: %s", str(e))
            raise ServiceError(f"Failed to initialize repository manager: {str(e)}")

    def clone_repository(self, url: str, path: str) -> RepositoryInfo:
        """Clone a repository.

        Args:
            url: Repository URL
            path: Local path to clone to

        Returns:
            Repository information

        Raises:
            ServiceError: If cloning fails
        """
        if not self._initialized:
            raise ServiceError("Repository manager not initialized")

        try:
            # Clone repository
            self._repo = Repo.clone_from(url, path)

            # Get repository info
            return self.get_repository_info(path)
        except Exception as e:
            self.logger.error("Failed to clone repository: %s", str(e))
            raise ServiceError(f"Failed to clone repository: {str(e)}")

    def get_repository_info(self, path: str) -> RepositoryInfo:
        """Get repository information.

        Args:
            path: Repository path

        Returns:
            Repository information

        Raises:
            ServiceError: If getting info fails
        """
        if not self._initialized:
            raise ServiceError("Repository manager not initialized")

        try:
            # Open repository
            repo = Repo(path)

            # Get repository info
            return RepositoryInfo(
                name=os.path.basename(path),
                local_path=path,
                branch=repo.active_branch.name,
                commit_hash=repo.head.commit.hexsha,
                is_dirty=repo.is_dirty(),
                metadata={
                    "remotes": [r.name for r in repo.remotes],
                    "tags": [t.name for t in repo.tags],
                    "head_message": repo.head.commit.message.strip(),
                },
            )
        except Exception as e:
            self.logger.error("Failed to get repository info: %s", str(e))
            raise ServiceError(f"Failed to get repository info: {str(e)}")

    def cleanup(self) -> None:
        """Clean up repository manager resources."""
        if self._repo:
            self._repo = None
        self._initialized = False
