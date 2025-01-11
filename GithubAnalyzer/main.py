from git import Repo
from .core.code_analyzer import CodeAnalyzer
from .core.database_utils import DatabaseManager

def analyze_repository(repo_url: str, local_path: str = "./temp_repo"):
    """
    Analyze a Git repository
    Args:
        repo_url: URL of the repository to analyze
        local_path: Local path to clone the repository to
    """
    try:
        # Clone repository
        print(f"Cloning {repo_url} to {local_path}")
        repo = Repo.clone_from(repo_url, local_path)
        
        # Initialize analyzer and database
        analyzer = CodeAnalyzer()
        db_manager = DatabaseManager()
        
        # Set current repository in database
        db_manager.set_current_repository(repo_url)
        
        # Analyze repository
        print("Starting repository analysis...")
        analyzer.analyze_repository(local_path)
        
        print("Analysis complete!")
        return True
        
    except Exception as e:
        print(f"Error analyzing repository: {e}")
        return False
    finally:
        # Cleanup
        if 'repo' in locals():
            repo.close()

def main():
    """Main entry point"""
    try:
        # Example repository to analyze
        repo_url = "https://github.com/example/repo.git"
        success = analyze_repository(repo_url)
        
        if success:
            print("Repository analysis completed successfully")
        else:
            print("Repository analysis failed")
            
    except Exception as e:
        print(f"Error in main: {e}")

if __name__ == "__main__":
    main() 