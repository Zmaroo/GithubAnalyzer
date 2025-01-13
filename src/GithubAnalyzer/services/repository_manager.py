import os
import shutil
from git import Repo
import logging
from typing import Dict, Any, Optional, List
from .database_utils import DatabaseManager
import traceback
from .models import (
    RepositoryInfo,
    ModuleInfo,
    DependencyInfo,
    AnalysisContext,
    AnalysisError,
    AnalysisStats
)
from .code_analyzer import CodeAnalyzer
from .documentation_analyzer import DocumentationAnalyzer
from .registry import BusinessTools
from .utils import setup_logger

logger = setup_logger(__name__)

class RepositoryManager:
    """Handles repository operations"""
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.tools = BusinessTools.create()

    def analyze_repo(self, repo_url: str, force_update: bool = False) -> Dict[str, Any]:
        """Analyze a repository and store results"""
        logger.info(f"Analyzing repository {repo_url}")
        try:
            repo_name = repo_url.split('/')[-1].replace('.git', '')
            local_path = os.path.join("./temp", repo_name)

            # Check if repo exists in database
            existing_repo = self.db_manager.get_repository_info()
            
            # Clear cache if forcing update or no database record exists
            if force_update or not existing_repo:
                self.db_manager.clear_cache(repo_name)
                logger.info("Cache cleared for fresh analysis")
                
                # Clean up local directory if it exists
                if os.path.exists(local_path):
                    shutil.rmtree(local_path)
                    logger.info("Cleaned up existing local repository")

            # Clone repository
            repo = self.clone_repository(repo_url, local_path)
            if not repo:
                raise Exception("Failed to clone repository")
            
            # Initialize analysis results
            analysis_results = {
                'name': repo_name,
                'url': repo_url,
                'local_path': local_path,
                'analysis': {}
            }
            
            # Analyze code structure using CodeAnalyzer
            code_analyzer = CodeAnalyzer(self.db_manager)
            code_analysis = code_analyzer.analyze_repository(local_path)
            if code_analysis:
                analysis_results['analysis']['code'] = code_analysis
                
            # Analyze documentation using DocumentationAnalyzer
            doc_analyzer = DocumentationAnalyzer()
            doc_analysis = doc_analyzer.analyze_file(local_path)
            if doc_analysis:
                analysis_results['analysis']['documentation'] = doc_analysis
                
            # Store results in databases
            self.db_manager.store_repository_info(
                repository_name=repo_name,
                repository_url=repo_url,
                local_path=local_path,
                metadata=analysis_results.get('analysis', {})
            )
            
            # Cache the results
            self.db_manager.store_in_cache(repo_name, 'analysis', analysis_results)
            
            return analysis_results

        except Exception as e:
            logger.error(f"Error analyzing repository: {e}")
            logger.error(traceback.format_exc())
            return {}

    def clone_repository(self, url: str, path: str) -> Optional[Repo]:
        """Clone and prepare repository"""
        try:
            if not os.path.exists(path):
                logger.info(f"Cloning repository from {url} to {path}")
                return Repo.clone_from(url, path)
            else:
                logger.info(f"Using existing repository at {path}")
                return Repo(path)
        except Exception as e:
            logger.error(f"Error cloning repository: {e}")
            logger.error(traceback.format_exc())
            return None

    def discover_files(self, repo_path: str) -> List[str]:
        """Discover repository files"""
        files = []
        try:
            for root, _, filenames in os.walk(repo_path):
                for filename in filenames:
                    files.append(os.path.join(root, filename))
            return files
        except Exception as e:
            logger.error(f"Error discovering files: {e}")
            logger.error(traceback.format_exc())
            return []

    def cleanup_repo(self, repo_path: str) -> bool:
        """Clean up repository files"""
        try:
            if os.path.exists(repo_path):
                shutil.rmtree(repo_path)
                logger.info(f"Cleaned up repository at {repo_path}")
            return True
        except Exception as e:
            logger.error(f"Error cleaning up repository: {e}")
            logger.error(traceback.format_exc())
            return False 