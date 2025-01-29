"""File service for GithubAnalyzer."""
import os
from pathlib import Path
from typing import List, Optional, Union, Set, Dict, Any

from GithubAnalyzer.utils.logging import get_logger
from GithubAnalyzer.models.core.file import FileInfo, FileFilterConfig
from GithubAnalyzer.services.analysis.parsers.language_service import LanguageService
from GithubAnalyzer.services.analysis.parsers.query_patterns import SPECIAL_FILENAMES
from GithubAnalyzer.services.analysis.parsers.custom_parsers import (
    get_custom_parser, CustomParser, EnvFileParser, RequirementsParser,
    GitignoreParser, EditorConfigParser, LockFileParser
)

logger = get_logger(__name__)

# Git-related files and directories to exclude
GIT_EXCLUDES: Set[str] = {
    '.git',
    '.gitignore',
    '.gitattributes',
    '.gitmodules',
    '.github',
    '.gitkeep'
}

# Build and dependency files to exclude
BUILD_EXCLUDES: Set[str] = {
    '__pycache__',
    '*.pyc',
    '*.pyo',
    '*.pyd',
    '.Python',
    'build',
    'develop-eggs',
    'dist',
    'downloads',
    'eggs',
    '.eggs',
    'lib',
    'lib64',
    'parts',
    'sdist',
    'var',
    'wheels',
    '*.egg-info',
    '.installed.cfg',
    '*.egg',
    'MANIFEST',
    'node_modules',
    '.env',
    '.venv',
    'env',
    'venv',
    'ENV',
    '.coverage',
    '.tox',
    '.pytest_cache',
    '.hypothesis',
    'target',  # Rust/Java build directory
    'out',     # Common output directory
    'bin',     # Binary directory
    'obj',     # .NET build directory
    'Debug',   # C++ debug build
    'Release', # C++ release build
    'cmake-build-*', # CMake build directories
    'vendor',  # Go/Ruby vendor directory
    'deps',    # Elixir/Erlang deps
    '_build',  # Elixir build directory
    'bazel-*', # Bazel build directories
    '.gradle', # Gradle build directory
    '.m2',     # Maven repository
    '.cargo',  # Cargo cache
    '.npm',    # NPM cache
    '.yarn',   # Yarn cache
    'bower_components', # Bower components
    'jspm_packages',    # JSPM packages
    '.pub-cache',       # Pub (Dart) cache
    '.dart_tool',       # Dart tool directory
    '.nuget',           # NuGet packages
    'packages',         # Various package directories
    'tmp',              # Temporary directory
    'temp',             # Temporary directory
    'cache',            # Cache directory
    'logs',             # Log directory
    'log',              # Log directory
    'coverage',         # Code coverage reports
    'report',           # Various reports
    'reports',          # Various reports
    'docs/_build',      # Sphinx documentation build
    'site-packages',    # Python site-packages
    '.ipynb_checkpoints', # Jupyter notebook checkpoints
    '.terraform',       # Terraform state directory
    '.serverless',      # Serverless framework directory
    '.next',            # Next.js build directory
    'dist-*',           # Distribution directories
    '.output',          # Output directory
    '.parcel-cache',    # Parcel bundler cache
    '.cache',           # Generic cache directory
    '.pytest_cache',    # Pytest cache
    '__snapshots__',    # Jest snapshots
    '.nyc_output',      # NYC code coverage
    '.docusaurus',      # Docusaurus build
    '.turbo',           # Turborepo cache
    '.svelte-kit',      # SvelteKit build
    '.astro',           # Astro build
    '.vercel',          # Vercel build
    '.netlify',         # Netlify build
    '.firebase',        # Firebase cache
    '.angular',         # Angular cache
    '.quasar',          # Quasar framework build
    '.umi',             # UmiJS build
    '.rpt2_cache',      # Rollup cache
    '.rts2_cache',      # Rollup cache
    '.fusion',          # Fusion.js build
    '.now',             # Now/Vercel directory
    '.serverless',      # Serverless build
    '.webpack',         # Webpack build
    '.dynamodb',        # Local DynamoDB
    '.vs',              # Visual Studio directory
    '.idea',            # IntelliJ directory
    '.settings',        # Eclipse settings
    '.project',         # Eclipse project
    '.classpath',       # Eclipse classpath
    '*.iml',            # IntelliJ module
    '*.ipr',            # IntelliJ project
    '*.iws',            # IntelliJ workspace
    '*.suo',            # Visual Studio user options
    '*.user',           # Visual Studio user settings
    '*.dbmdl',          # Visual Studio database model
    '*.jfm',            # Visual Studio database journal
    'local.settings.json', # Azure Functions local settings
    '.DS_Store',        # macOS metadata
    'Thumbs.db',        # Windows thumbnail cache
    'desktop.ini',      # Windows desktop settings
    '*.swp',            # Vim swap file
    '*.swo',            # Vim swap file
    '*~',               # Backup files
    '*.bak',            # Backup files
    '*.orig',           # Original files from merge conflicts
    '*.log',            # Log files
    '*.pid',            # Process ID files
    '*.seed',           # Seed files
    '*.pid.lock',       # Process ID lock files
    '*.lcov',           # LCOV coverage files
    '*.tsbuildinfo',    # TypeScript build info
    '.eslintcache',     # ESLint cache
    '.stylelintcache',  # Stylelint cache
    '.sass-cache',      # Sass cache
    '.php_cs.cache',    # PHP CS Fixer cache
    '.phpunit.result.cache', # PHPUnit cache
    'composer.phar',    # Composer PHAR
    '.web-server-pid',  # Web server PID
    '.buildpath',       # Eclipse buildpath
    '.cproject',        # Eclipse C project
    '.loadpath',        # Eclipse load path
    '.recommenders',    # Eclipse recommenders
    '.metadata',        # Eclipse metadata
    '.apt_generated',   # Eclipse APT
    '.sts4-cache',      # Spring Tool Suite cache
    '.history',         # VS Code history
    '.ionide',          # Ionide-vim
    '.metals',          # Metals (Scala)
    '.bloop',           # Bloop (Scala)
    '.ensime',          # ENSIME (Scala)
    '.ensime_cache',    # ENSIME cache
    'codegen',          # Generated code directory
    'generated',        # Generated code directory
    'gen',              # Generated code directory
    '.gen',             # Generated code directory
    'auto-generated',   # Generated code directory
    'protos',           # Protocol buffer definitions
    'schemas',          # Schema definitions
    'swagger',          # Swagger/OpenAPI definitions
    'openapi',          # OpenAPI definitions
    'graphql',          # GraphQL definitions
    'thrift',           # Thrift definitions
    'proto',            # Protocol buffer definitions
    'fixtures',         # Test fixtures
    'mocks',            # Test mocks
    'stubs',            # Test stubs
    'test-results',     # Test results
    'test-output',      # Test output
    'test-reports',     # Test reports
    'benchmarks',       # Benchmark results
    'profiling',        # Profiling data
    'traces',           # Trace data
    'artifacts',        # Build artifacts
    'assets',           # Static assets
    'static',           # Static files
    'public',           # Public files
    'resources',        # Resource files
    'examples',         # Example code
    'samples',          # Sample code
    'demo',             # Demo code
    'docs',             # Documentation
    'doc',              # Documentation
    'wiki',             # Wiki files
    'scripts',          # Scripts directory
    'tools',            # Tools directory
    'utils',            # Utilities directory
    'config',           # Configuration directory
    'configs',          # Configuration directory
    'settings',         # Settings directory
    'templates',        # Template files
    'layouts',          # Layout files
    'themes',           # Theme files
    'styles',           # Style files
    'css',              # CSS files
    'js',               # JavaScript files
    'images',           # Image files
    'img',              # Image files
    'fonts',            # Font files
    'icons',            # Icon files
    'media',            # Media files
    'videos',           # Video files
    'audio',            # Audio files
    'sounds',           # Sound files
    'music',            # Music files
    'locales',          # Localization files
    'translations',     # Translation files
    'i18n',             # Internationalization files
    'l10n',             # Localization files
    'messages',         # Message files
    'emails',           # Email templates
    'views',            # View templates
    'partials',         # Partial templates
    'components',       # UI components
    'modules',          # Module files
    'packages',         # Package files
    'plugins',          # Plugin files
    'addons',           # Addon files
    'extensions',       # Extension files
    'migrations',       # Database migrations
    'seeds',            # Database seeds
    'dumps',            # Database dumps
    'backup',           # Backup files
    'backups',          # Backup files
    'archive',          # Archive files
    'archives',         # Archive files
    'old',              # Old files
    'new',              # New files
    'temp',             # Temporary files
    'tmp',              # Temporary files
    'draft',            # Draft files
    'drafts',           # Draft files
    'local',            # Local files
    'private',          # Private files
    'secret',           # Secret files
    'secrets',          # Secret files
    'sensitive',        # Sensitive files
    'confidential',     # Confidential files
    'restricted',       # Restricted files
    'internal',         # Internal files
    'external',         # External files
    'third-party',      # Third-party files
    'vendor',           # Vendor files
    'deps',             # Dependency files
    'dependencies',     # Dependency files
    'node_modules',     # Node.js modules
    'bower_components', # Bower components
    'jspm_packages',    # JSPM packages
    'packages',         # Package files
    'composer.phar',    # Composer PHAR
    '.phar',            # PHP archives
    '.phpt',            # PHP test files
    '.phpunit',         # PHPUnit files
    '.php_cs',          # PHP CS Fixer
    '.php_cs.dist',     # PHP CS Fixer dist
    '.phpcs.xml',       # PHP_CodeSniffer
    '.phpcs.xml.dist',  # PHP_CodeSniffer dist
    '.phplint.yml',     # PHP Lint
    '.phpstan.neon',    # PHPStan
    '.phpstan.neon.dist', # PHPStan dist
    '.phpmd.xml',       # PHP Mess Detector
    '.phpmd.xml.dist',  # PHP Mess Detector dist
    '.php-version',     # PHP version
    '.ruby-version',    # Ruby version
    '.node-version',    # Node.js version
    '.nvmrc',           # NVM config
    '.tool-versions',   # asdf version manager
    '.python-version',  # pyenv version
    '.java-version',    # jEnv version
    'pom.xml',          # Maven POM
    'build.gradle',     # Gradle build
    'build.sbt',        # SBT build
    'project.clj',      # Leiningen project
    'mix.exs',          # Mix project
    'rebar.config',     # Rebar config
    'Gemfile',          # Bundler gemfile
    'Gemfile.lock',     # Bundler lockfile
    'package.json',     # NPM package
    'package-lock.json', # NPM lockfile
    'yarn.lock',        # Yarn lockfile
    'pnpm-lock.yaml',   # pnpm lockfile
    'composer.json',    # Composer package
    'composer.lock',    # Composer lockfile
    'poetry.lock',      # Poetry lockfile
    'Pipfile',          # Pipenv file
    'Pipfile.lock',     # Pipenv lockfile
    'requirements.txt', # Python requirements
    'go.mod',           # Go modules
    'go.sum',           # Go checksum
    'Cargo.toml',       # Cargo manifest
    'Cargo.lock',       # Cargo lockfile
    'mix.lock',         # Mix lockfile
    'elm-package.json', # Elm package
    'elm-stuff',        # Elm stuff
    '.terraform.lock.hcl', # Terraform lock
    'yarn-error.log',   # Yarn error log
    'npm-debug.log',    # NPM debug log
    '.npmrc',           # NPM config
    '.yarnrc',          # Yarn config
    '.bowerrc',         # Bower config
    '.eslintrc',        # ESLint config
    '.eslintrc.js',     # ESLint config
    '.eslintrc.json',   # ESLint config
    '.eslintrc.yml',    # ESLint config
    '.eslintignore',    # ESLint ignore
    '.prettierrc',      # Prettier config
    '.prettierrc.js',   # Prettier config
    '.prettierrc.json', # Prettier config
    '.prettierrc.yml',  # Prettier config
    '.prettierignore',  # Prettier ignore
    '.stylelintrc',     # Stylelint config
    '.stylelintrc.js',  # Stylelint config
    '.stylelintrc.json', # Stylelint config
    '.stylelintrc.yml', # Stylelint config
    '.stylelintignore', # Stylelint ignore
    'tslint.json',      # TSLint config
    'tsconfig.json',    # TypeScript config
    'jsconfig.json',    # JavaScript config
    'babel.config.js',  # Babel config
    '.babelrc',         # Babel config
    '.babelrc.js',      # Babel config
    'webpack.config.js', # Webpack config
    'rollup.config.js', # Rollup config
    'jest.config.js',   # Jest config
    'karma.conf.js',    # Karma config
    'protractor.conf.js', # Protractor config
    'cypress.json',     # Cypress config
    '.browserslistrc',  # Browserslist config
    '.editorconfig',    # EditorConfig
    '.dockerignore',    # Docker ignore
    'Dockerfile',       # Dockerfile
    'docker-compose.yml', # Docker Compose
    'docker-compose.yaml', # Docker Compose
    '.env',             # Environment variables
    '.env.local',       # Local env variables
    '.env.development', # Development env
    '.env.test',        # Test env
    '.env.production',  # Production env
    '.env.example',     # Example env
    '.env.sample',      # Sample env
    '.env.template',    # Template env
    'LICENSE',          # License file
    'LICENSE.md',       # License file
    'LICENSE.txt',      # License file
    'COPYING',          # License file
    'COPYING.md',       # License file
    'COPYING.txt',      # License file
    'README',           # README file
    'README.md',        # README file
    'README.txt',       # README file
    'CHANGELOG',        # Changelog file
    'CHANGELOG.md',     # Changelog file
    'CHANGELOG.txt',    # Changelog file
    'CONTRIBUTING',     # Contributing guide
    'CONTRIBUTING.md',  # Contributing guide
    'CONTRIBUTING.txt', # Contributing guide
    'CODE_OF_CONDUCT', # Code of conduct
    'CODE_OF_CONDUCT.md', # Code of conduct
    'CODE_OF_CONDUCT.txt', # Code of conduct
    'SECURITY',         # Security policy
    'SECURITY.md',      # Security policy
    'SECURITY.txt',     # Security policy
    'AUTHORS',          # Authors file
    'AUTHORS.md',       # Authors file
    'AUTHORS.txt',      # Authors file
    'CONTRIBUTORS',     # Contributors file
    'CONTRIBUTORS.md',  # Contributors file
    'CONTRIBUTORS.txt', # Contributors file
    'PATENTS',          # Patents file
    'PATENTS.md',       # Patents file
    'PATENTS.txt',      # Patents file
    'VERSION',          # Version file
    'VERSION.md',       # Version file
    'VERSION.txt',      # Version file
    '.version',         # Version file
    '.ruby-version',    # Ruby version
    '.python-version',  # Python version
    '.node-version',    # Node.js version
    '.java-version',    # Java version
    '.php-version',     # PHP version
    '.go-version',      # Go version
    '.tool-versions',   # asdf version manager
    '.nvmrc',           # Node Version Manager
    '.ruby-gemset',     # RVM gemset
    'Procfile',         # Heroku Procfile
    'app.json',         # Heroku app
    'now.json',         # Vercel config
    'vercel.json',      # Vercel config
    'netlify.toml',     # Netlify config
    'firebase.json',    # Firebase config
    '.firebaserc',      # Firebase config
    'serverless.yml',   # Serverless config
    'serverless.yaml',  # Serverless config
    '.travis.yml',      # Travis CI config
    '.circleci',        # Circle CI config
    '.github',          # GitHub config
    '.gitlab-ci.yml',   # GitLab CI config
    'azure-pipelines.yml', # Azure Pipelines
    'jenkins',          # Jenkins config
    'Jenkinsfile',      # Jenkins pipeline
    'sonar-project.properties', # SonarQube
    '.codecov.yml',     # Codecov config
    'codecov.yml',      # Codecov config
    '.coveralls.yml',   # Coveralls config
    'appveyor.yml',     # AppVeyor config
    'bamboo-specs',     # Bamboo specs
    'bitbucket-pipelines.yml', # Bitbucket
    'buildspec.yml',    # AWS CodeBuild
    'cloudbuild.yaml',  # Cloud Build
    'codeship-services.yml', # Codeship
    'codeship-steps.yml', # Codeship
    'wercker.yml',      # Wercker
    'renovate.json',    # Renovate
    '.snyk',            # Snyk
    'helm',             # Helm charts
    'k8s',              # Kubernetes
    'kubernetes',       # Kubernetes
    'manifests',        # K8s manifests
    'charts',           # Helm charts
    'terraform',        # Terraform
    'ansible',          # Ansible
    'puppet',           # Puppet
    'chef',             # Chef
    'vagrant',          # Vagrant
    '.vagrant',         # Vagrant
    'Vagrantfile',      # Vagrant file
}

# Editor and IDE files to exclude
EDITOR_EXCLUDES: Set[str] = {
    '.idea',
    '.vscode',
    '*.swp',
    '*.swo',
    '*~',
    '.DS_Store',
    'Thumbs.db',
    '.vs',
    '.settings',
    '.project',
    '.classpath',
    '*.iml',
    '*.ipr',
    '*.iws',
    '*.suo',
    '*.user',
    '*.dbmdl',
    '*.jfm',
    '.editorconfig',
    '.sublime-project',
    '.sublime-workspace',
    '*.sublime-*',
    '.atom',
    '.brackets.json',
    '.komodoproject',
    '*.komodoproject',
    '.komodotools',
    '.netbeans',
    'nbproject',
    '.eclipse',
    '.settings',
    '.project',
    '.buildpath',
    '.tm_properties',
    '.tern-project',
    '.tags',
    '.tags_sorted_by_file',
    '.gemtags',
    '.ctags',
    '.rgignore',
    '.agignore',
    '.ignore',
    '.ac-php-conf.json',
    '.dir-locals.el',
    '*.code-workspace',
    '.history',
    '.ionide',
    '.metals',
    '.bloop',
    '.ensime',
    '.ensime_cache',
    '.vim',
    '.netrwhist',
    'Session.vim',
    'tags',
    'TAGS',
    'cscope.*',
    '*.taghl',
    '*.tags',
    '*.vtags',
    '*.ptags',
    '*.gtags',
    '*.htags',
    '.notags',
    '.ropeproject',
    '.spyderproject',
    '.spyproject',
    '.vimspector.json',
    '.ccls-cache',
    '.clangd',
    '.lsp',
    '.jj',
    '.idea_modules',
    '.fleet',
    '.devcontainer',
    '.mutagen.yml',
    '.mutagen.yml.lock',
    '.nova',
    '.vscode-test',
    '.vscodeignore',
    '.vscode-test-web',
    '.factorypath',
    '.apt_generated',
    '.apt_generated_tests',
    '.sts4-cache',
    '.jdt.ls-java-project',
    '.jshintrc',
    '.jscsrc',
    '.tern-config',
    '.jsbeautifyrc',
    '.modernizrrc',
    '.sass-lint.yml',
    '.csscomb.json',
    '.csslintrc',
    '.htmlhintrc',
    '.markdownlint.json',
    '.markdownlintrc',
    '.mdlrc',
    '.rubocop.yml',
    '.rubocop_todo.yml',
    '.solhint.json',
    '.soliumrc.json',
    '.soliumignore',
    '.yamllint',
    '.yamllint.yml',
    '.dccache',
    '.idea_codeStyleSettings.xml',
    '.idea_modules.xml',
    '.idea_workspace.xml',
    '.idea_tasks.xml',
    '.idea_dictionaries',
    '.idea_shelf',
    '.idea_caches',
    '.idea_libraries',
    '.idea_artifacts',
    '.idea_dataSources',
    '.idea_sqlDataSources',
    '.idea_dynamic.xml',
    '.idea_uiDesigner.xml',
    '.idea_gradle.xml',
    '.idea_misc.xml',
    '.idea_modules.xml',
    '.idea_vcs.xml',
    '.idea_jsLibraryMappings.xml',
    '.idea_kotlinc.xml',
    '.idea_assetWizardSettings.xml',
    '.idea_navEditor.xml',
    '.idea_render.experimental.xml',
    '.idea_scopes',
    '.idea_copyright',
    '.idea_inspectionProfiles',
    '.idea_runConfigurations',
    '.idea_codeStyles',
    '.idea_encodings.xml',
    '.idea_compiler.xml',
    '.idea_jarRepositories.xml',
    '.idea_aws.xml',
    '.idea_deploymentTargetDropDown.xml',
    '.idea_migrations.xml',
    '.idea_workspace.xml',
    '.idea_tasks.xml',
    '.idea_usage.statistics.xml',
    '.idea_dictionaries',
    '.idea_shelf',
    '.idea_contentModel.xml',
    '.idea_dataSources.xml',
    '.idea_dataSources.local.xml',
    '.idea_sqlDataSources.xml',
    '.idea_dynamic.xml',
    '.idea_uiDesigner.xml',
    '.idea_modules.xml',
    '.idea_gradle.xml',
    '.idea_libraries',
    '.idea_caches',
    '.idea_artifacts',
    '.idea_compiler.xml',
    '.idea_jarRepositories.xml',
    '.idea_misc.xml',
    '.idea_vcs.xml',
    '.idea_jsLibraryMappings.xml',
    '.idea_kotlinc.xml',
    '.idea_assetWizardSettings.xml',
    '.idea_navEditor.xml',
    '.idea_render.experimental.xml'
}

# Default exclude patterns
DEFAULT_EXCLUDES: Set[str] = GIT_EXCLUDES | BUILD_EXCLUDES | EDITOR_EXCLUDES

class FileService:
    """Service for file operations."""
    
    def __init__(self, base_path: Optional[Union[str, Path]] = None):
        """Initialize the file service.
        
        Args:
            base_path: Optional base path for relative path resolution
        """
        self.base_path = Path(base_path) if base_path else None
        self._language_service = LanguageService()
        logger.debug({
            "message": "FileService initialized",
            "context": {
                'base_path': str(self.base_path)
            }
        })
        
    def get_repository_files(self, repo_path: Union[str, Path]) -> List[FileInfo]:
        """Get all files from a repository directory.
        
        Args:
            repo_path: Path to the repository directory
            
        Returns:
            List of FileInfo objects for each file
        """
        repo_path = Path(repo_path)
        
        # Find repository root (directory containing .git)
        repo_root = repo_path
        while repo_root.parent != repo_root:
            if (repo_root / '.git').exists():
                break
            repo_root = repo_root.parent
            
        logger.debug({
            "message": "Found repository root",
            "context": {
                "repo_path": str(repo_path),
                "repo_root": str(repo_root)
            }
        })
        
        # Use custom filter config for repository files
        filter_config = FileFilterConfig(
            exclude_paths=list(DEFAULT_EXCLUDES)
        )
        
        return self.list_files(repo_path, filter_config)
        
    def list_files(self, root_path: Path, filter_config: Optional[FileFilterConfig] = None) -> List[FileInfo]:
        """List files in a directory, optionally filtered by configuration.
        
        Args:
            root_path: Root directory to start searching from.
            filter_config: Optional configuration for filtering files.
            
        Returns:
            List of FileInfo objects for matching files.
            
        Raises:
            FileNotFoundError: If the root path does not exist.
            PermissionError: If a directory cannot be accessed.
        """
        try:
            files = []
            for file_path in root_path.rglob('*'):
                if not file_path.is_file():
                    continue
                    
                # Skip files based on filter config
                if filter_config and not self._matches_filter(file_path, filter_config):
                    continue
                
                # Skip binary files early
                if self._is_binary_file(file_path):
                    continue
                
                # Get language from LanguageService
                language = self._detect_language(file_path)
                
                # Create FileInfo with detected language
                file_info = FileInfo(
                    path=file_path,
                    language=language,
                    metadata={
                        'size': file_path.stat().st_size,
                        'modified': file_path.stat().st_mtime,
                        'is_special': file_path.name in SPECIAL_FILENAMES
                    }
                )
                files.append(file_info)
                
            logger.debug({
                "message": "Files listed successfully",
                "context": {
                    "root_path": str(root_path),
                    "filter_config": filter_config.__dict__ if filter_config else None,
                    "file_count": len(files)
                }
            })
            return files
            
        except (FileNotFoundError, PermissionError) as e:
            logger.error({
                "message": "Error listing files",
                "context": {
                    "root_path": str(root_path),
                    "filter_config": filter_config.__dict__ if filter_config else None,
                    "error": str(e)
                }
            })
            raise
            
    def _is_binary_file(self, file_path: Union[str, Path]) -> bool:
        """Check if a file is binary.
        
        Args:
            file_path: Path to the file to check.
            
        Returns:
            True if the file is binary, False otherwise.
        """
        try:
            with open(file_path, 'rb') as f:
                # Read first 1024 bytes to check for null bytes
                chunk = f.read(1024)
                return b'\x00' in chunk
        except (FileNotFoundError, PermissionError):
            return False
            
    def read_file(self, file_path: Union[str, Path]) -> str:
        """Read the contents of a file.
        
        Args:
            file_path: Path to the file to read.
            
        Returns:
            The contents of the file as a string.
            
        Raises:
            FileNotFoundError: If the file does not exist.
            PermissionError: If the file cannot be read.
            ValueError: If the file is binary.
        """
        try:
            full_path = self.base_path / file_path
            
            # Check if file is binary
            if self._is_binary_file(full_path):
                logger.debug({
                    "message": "Skipping binary file",
                    "context": {
                        "file_path": str(file_path)
                    }
                })
                raise ValueError("Cannot read binary file")
                
            with open(full_path, 'r') as f:
                content = f.read()
                
            logger.debug({
                "message": "File read successfully",
                "context": {
                    "file_path": str(file_path),
                    "size_bytes": len(content)
                }
            })
            return content
            
        except (FileNotFoundError, PermissionError) as e:
            logger.error({
                "message": "Error reading file",
                "context": {
                    "file_path": str(file_path),
                    "error": str(e)
                }
            })
            raise
            
    def write_file(self, file_path: Union[str, Path], content: str) -> None:
        """Write content to a file.
        
        Args:
            file_path: Path to the file to write.
            content: Content to write to the file.
            
        Raises:
            PermissionError: If the file cannot be written.
            OSError: If the directory does not exist.
        """
        try:
            full_path = self.base_path / file_path
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'w') as f:
                f.write(content)
                
            logger.debug({
                "message": "File written successfully",
                "context": {
                    "file_path": str(file_path),
                    "size_bytes": len(content)
                }
            })
            
        except (PermissionError, OSError) as e:
            logger.error({
                "message": "Error writing file",
                "context": {
                    "file_path": str(file_path),
                    "error": str(e)
                }
            })
            raise
            
    def _matches_filter(self, file_path: Path, filter_config: FileFilterConfig) -> bool:
        """Check if a file matches the filter configuration.
        
        Args:
            file_path: Path to the file to check.
            filter_config: Configuration for filtering files.
            
        Returns:
            True if the file matches the filter, False otherwise.
        """
        if filter_config.exclude_paths:
            for pattern in filter_config.exclude_paths:
                if file_path.match(pattern):
                    return False
                    
        if filter_config.include_paths:
            for pattern in filter_config.include_paths:
                if file_path.match(pattern):
                    return True
            return False
            
        return True
        
    def _detect_language(self, file_path: Path) -> str:
        """Detect the programming language of a file based on its extension.
        
        Args:
            file_path: Path to the file to check.
            
        Returns:
            The detected programming language, or 'plaintext' if not recognized.
        """
        try:
            # First check if we have a custom parser for this file
            custom_parser = get_custom_parser(str(file_path))
            if custom_parser:
                # For files with custom parsers, return their custom type
                parser_type = custom_parser.__class__.__name__
                if parser_type == 'EnvFileParser':
                    return 'env'
                elif parser_type == 'RequirementsParser':
                    return 'requirements'
                elif parser_type == 'GitignoreParser':
                    return 'gitignore'
                elif parser_type == 'EditorConfigParser':
                    return 'editorconfig'
                elif parser_type == 'LockFileParser':
                    return 'lockfile'
            
            # If no custom parser or it's not a recognized type,
            # try tree-sitter language detection
            return self._language_service.get_language_for_file(str(file_path))
        except ValueError:
            # If language detection fails, return plaintext
            return 'plaintext'
        
    def validate_language(self, file_info: FileInfo, expected_type: str) -> bool:
        """Validate that a file is of the expected language type.
        
        Args:
            file_info: FileInfo object to validate.
            expected_type: Expected language type.
            
        Returns:
            True if the file matches the expected type, False otherwise.
        """
        if isinstance(file_info.language, str):
            return file_info.language == expected_type
        return str(file_info.language) == expected_type 

    def _should_exclude(self, file_path: Path) -> bool:
        """Check if a file should be excluded based on default patterns.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if the file should be excluded
        """
        # Check each path component against exclude patterns
        for part in file_path.parts:
            if part in DEFAULT_EXCLUDES:
                return True
                
            # Check wildcard patterns
            for pattern in DEFAULT_EXCLUDES:
                if '*' in pattern and Path(part).match(pattern):
                    return True
                    
        return False 

    def has_custom_parser(self, file_path: Union[str, Path]) -> bool:
        """Check if a file has a custom parser available.
        
        Args:
            file_path: Path to the file to check.
            
        Returns:
            True if a custom parser is available for this file type.
        """
        return get_custom_parser(str(file_path)) is not None 