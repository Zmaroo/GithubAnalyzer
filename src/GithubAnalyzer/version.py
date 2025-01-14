"""Version information"""

import os
from typing import Tuple

import pkg_resources


def get_version() -> Tuple[str, str]:
    """Get package and git versions"""
    try:
        version = pkg_resources.get_distribution("GithubAnalyzer").version
    except pkg_resources.DistributionNotFound:
        version = "0.0.0"

    try:
        from git import Repo

        # Go up three levels: src/GithubAnalyzer/version.py -> src/GithubAnalyzer -> src -> root
        repo = Repo(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        git_version = repo.head.commit.hexsha[:7]
    except:
        git_version = "unknown"

    return version, git_version


__version__, __git_version__ = get_version()
