from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
import re
from pathlib import Path
from ..config.config import LANGUAGE_MAP
import logging
import yaml
from dotenv import dotenv_values
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

# Try to import jproperties, fallback to javaproperties
try:
    from jproperties import Properties
    PROPERTIES_PARSER = "jproperties"
except ImportError:
    try:
        import javaproperties
        PROPERTIES_PARSER = "javaproperties"
    except ImportError:
        PROPERTIES_PARSER = None
        logger.warning("Neither jproperties nor javaproperties is installed. Properties file parsing will be limited.")

class BaseFileParser(ABC):
    def __init__(self):
        self.current_file = None

    @abstractmethod
    def parse(self, content: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def supported_extensions(self) -> List[str]:
        pass

    def set_current_file(self, filepath: str) -> None:
        """Set the current file being parsed"""
        self.current_file = filepath

class CustomParserRegistry:
    """Registry to manage parsers for non-tree-sitter supported files"""
    
    def __init__(self):
        self.parsers = {}
        self.tree_sitter_languages = self._get_tree_sitter_languages()
        
    def _get_tree_sitter_languages(self) -> List[str]:
        """Get list of languages supported by tree-sitter"""
        # Use unique values from LANGUAGE_MAP
        return list(set(LANGUAGE_MAP.values()))
        
    def register_parser(self, parser: BaseFileParser):
        """Register a custom parser for non-tree-sitter files"""
        for ext in parser.supported_extensions():
            if ext in LANGUAGE_MAP:
                logger.warning(
                    f"Skipping registration of parser for {ext} - "
                    "already handled by tree-sitter"
                )
                continue
            self.parsers[ext] = parser
            
    def _is_tree_sitter_extension(self, ext: str) -> bool:
        """Check if file extension is handled by tree-sitter"""
        return ext in LANGUAGE_MAP

    def get_parser(self, file_path: str) -> Optional[BaseFileParser]:
        """Get appropriate parser for a file"""
        path = Path(file_path)
        # First try exact filename match
        for parser in self.parsers.values():
            if path.name in parser.supported_extensions():
                return parser
        # Then try extension match
        return self.parsers.get(path.suffix)

class ConfigParser(BaseFileParser):
    def supported_extensions(self) -> List[str]:
        return ['.ini', '.conf']  # Remove .yaml, .yml, .toml, .json since they're handled by tree-sitter
        
    def parse(self, content: str) -> Dict[str, Any]:
        """Parse various configuration file formats"""
        ext = Path(self.current_file).suffix
        
        try:
            if ext in ['.ini', '.conf']:
                return self._parse_ini(content)
        except Exception as e:
            logger.error(f"Error parsing config file {self.current_file}: {e}")
            return {'config': {}, 'error': str(e)}

    def _parse_ini(self, content: str) -> Dict[str, Any]:
        """Parse INI-style configuration files"""
        config = {}
        current_section = 'default'
        
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            if line.startswith('[') and line.endswith(']'):
                current_section = line[1:-1]
                config[current_section] = {}
            elif '=' in line:
                key, value = line.split('=', 1)
                section = config.get(current_section, {})
                section[key.strip()] = value.strip()
                config[current_section] = section
                
        return {'config': config}

class DocContentParser(BaseFileParser):
    """Parser for documentation content and formatting (not code structure)
    
    While tree-sitter handles code structure including docstring locations,
    this parser handles the semantic content within documentation:
    - reST formatting
    - Parameter descriptions
    - Return type documentation
    - Example formatting
    - Cross-references
    """
    def supported_extensions(self) -> List[str]:
        return ['.rst', '.txt']
        
    def parse(self, content: str) -> Dict[str, Any]:
        """Parse documentation content and formatting
        
        This complements tree-sitter's structural parsing by handling
        the semantic content within documentation strings and files.
        """
        docs = {
            'sections': [],
            'parameters': [],
            'returns': [],
            'examples': [],
            'references': []
        }
        
        # Parse reStructuredText sections
        if self.current_file.endswith('.rst'):
            sections = re.split(r'\n{2,}', content)
            current_section = {'title': '', 'content': []}
            
            for section in sections:
                if re.match(r'^={3,}$', section.splitlines()[-1]):
                    if current_section['content']:
                        docs['sections'].append(current_section)
                    current_section = {
                        'title': section.splitlines()[0],
                        'content': []
                    }
                else:
                    current_section['content'].append(section)
                    
            if current_section['content']:
                docs['sections'].append(current_section)
                
        # Parse plain text documentation
        else:
            docs['sections'] = [{'content': content}]
            
        return docs

class BuildSystemParser(BaseFileParser):
    """Parser for build system and package files"""
    def supported_extensions(self) -> List[str]:
        return [
            'requirements.txt',  # Python requirements
            # Removed: CMakeLists.txt, .cmake (use tree-sitter-cmake)
            # Removed: build.gradle (use tree-sitter-groovy)
            # Removed: Gemfile (use tree-sitter-ruby)
        ]

    def parse(self, content: str) -> Dict[str, Any]:
        """Parse build system files"""
        filename = Path(self.current_file).name.lower()
        
        try:
            if filename in ['makefile', 'makefile.in']:
                return self._parse_makefile(content)
            elif filename.endswith('.cmake') or filename == 'cmakelists.txt':
                return self._parse_cmake(content)
            elif filename == 'requirements.txt':
                return self._parse_requirements(content)
            elif filename.endswith('.gradle'):
                return self._parse_gradle(content)
            elif filename == 'gemfile':
                return self._parse_gemfile(content)
            
            return {'error': f'Unsupported build file: {filename}'}
        except Exception as e:
            logger.error(f"Error parsing build file {filename}: {e}")
            return {'error': str(e)}

    def _parse_makefile(self, content: str) -> Dict[str, Any]:
        """Parse Makefile content"""
        result = {
            'targets': {},
            'variables': {},
            'includes': []
        }
        
        current_target = None
        
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            # Parse include statements
            if line.startswith('include'):
                result['includes'].append(line.split(None, 1)[1])
                
            # Parse variable definitions
            elif ':=' in line or '=' in line:
                op = ':=' if ':=' in line else '='
                key, value = line.split(op, 1)
                result['variables'][key.strip()] = value.strip()
                
            # Parse targets
            elif ':' in line and not line.startswith('.'):
                target, deps = line.split(':', 1)
                current_target = target.strip()
                result['targets'][current_target] = {
                    'dependencies': [d.strip() for d in deps.split()],
                    'commands': []
                }
                
            # Parse target commands
            elif line.startswith('\t') and current_target:
                result['targets'][current_target]['commands'].append(line.lstrip())
                
        return result

    def _parse_cmake(self, content: str) -> Dict[str, Any]:
        """Parse CMake content"""
        result = {
            'commands': [],
            'variables': {},
            'targets': [],
            'includes': []
        }
        
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            # Parse commands
            if line.startswith(('add_executable', 'add_library', 'add_subdirectory')):
                result['commands'].append(line)
                
            # Parse set commands
            elif line.startswith('set('):
                var_match = re.match(r'set\((\w+)\s+(.+)\)', line)
                if var_match:
                    result['variables'][var_match.group(1)] = var_match.group(2)
                    
            # Parse includes
            elif line.startswith(('include(', 'include_directories(')):
                result['includes'].append(line)
                
            # Parse targets
            elif line.startswith(('add_executable(', 'add_library(')):
                result['targets'].append(line)
                
        return result

    def _parse_requirements(self, content: str) -> Dict[str, Any]:
        """Parse Python requirements.txt"""
        requirements = []
        
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            # Parse package specifications
            if '>=' in line or '==' in line or '<=' in line:
                package, version = re.split(r'>=|==|<=', line, 1)
                requirements.append({
                    'package': package.strip(),
                    'version': version.strip(),
                    'constraint': re.search(r'>=|==|<=', line).group()
                })
            else:
                requirements.append({
                    'package': line.strip(),
                    'version': None,
                    'constraint': None
                })
                
        return {'requirements': requirements}

    def _parse_gradle(self, content: str) -> Dict[str, Any]:
        """Parse Gradle build files"""
        result = {
            'plugins': [],
            'dependencies': [],
            'repositories': [],
            'tasks': []
        }
        
        current_block = None
        current_block_content = []
        
        for line in content.splitlines():
            line = line.strip()
            
            if not line or line.startswith('//'):
                continue
                
            # Detect block start
            if line.endswith('{'):
                current_block = line.split()[0]
                current_block_content = []
            # Detect block end
            elif line == '}' and current_block:
                if current_block == 'dependencies':
                    result['dependencies'].extend(self._parse_gradle_dependencies(current_block_content))
                elif current_block == 'repositories':
                    result['repositories'].extend(current_block_content)
                elif current_block == 'plugins':
                    result['plugins'].extend(current_block_content)
                current_block = None
                current_block_content = []
            # Collect block content
            elif current_block:
                current_block_content.append(line)
                
        return result

    def _parse_gradle_dependencies(self, lines: List[str]) -> List[Dict[str, str]]:
        """Parse Gradle dependency declarations"""
        dependencies = []
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('//'):
                continue
                
            # Parse dependency declaration
            match = re.match(r'(\w+)\s*[\'"]([\w\.-]+:[\w\.-]+:[\w\.-]+)[\'"]', line)
            if match:
                dependencies.append({
                    'type': match.group(1),
                    'dependency': match.group(2)
                })
                
        return dependencies

    def _parse_gemfile(self, content: str) -> Dict[str, Any]:
        """Parse Ruby Gemfile"""
        result = {
            'source': None,
            'gems': [],
            'groups': {}
        }
        
        current_group = None
        
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            # Parse source
            if line.startswith('source'):
                result['source'] = line.split("'")[1]
                
            # Parse gem declarations
            elif line.startswith('gem'):
                gem_info = self._parse_gem_line(line)
                if current_group:
                    if current_group not in result['groups']:
                        result['groups'][current_group] = []
                    result['groups'][current_group].append(gem_info)
                else:
                    result['gems'].append(gem_info)
                    
            # Parse group blocks
            elif line.startswith('group'):
                current_group = line.split()[1].rstrip(' do').strip(":'")
            elif line == 'end':
                current_group = None
                
        return result

    def _parse_gem_line(self, line: str) -> Dict[str, str]:
        """Parse a single gem declaration"""
        parts = line.split(',')
        gem_name = parts[0].split()[1].strip("'\"")
        
        result = {'name': gem_name}
        
        for part in parts[1:]:
            if '=>' in part:
                key, value = part.split('=>')
                result[key.strip()] = value.strip().strip("'\"")
                
        return result

class CIConfigParser(BaseFileParser):
    """Parser for CI/CD configuration files"""
    def supported_extensions(self) -> List[str]:
        return [
            '.gitlab-ci.yml',  # GitLab CI
            '.travis.yml',  # Travis CI
            '.circleci/config.yml',  # CircleCI
            'Jenkinsfile',  # Jenkins pipeline
            '.github/workflows/',  # GitHub Actions
            'azure-pipelines.yml'  # Azure Pipelines
        ]

    def parse(self, content: str) -> Dict[str, Any]:
        """Parse CI configuration files with semantic understanding"""
        if not content.strip():
            return {'error': 'Empty file'}

        try:
            filename = Path(self.current_file).name.lower()
            filepath = str(Path(self.current_file))

            if 'jenkinsfile' in filename.lower():
                return self._parse_jenkinsfile(content)
            elif '.github/workflows' in filepath:
                return self._parse_github_actions(content)
            elif any(filename.endswith(ext) for ext in ['.yml', '.yaml']):
                try:
                    ci_config = yaml.safe_load(content)
                    if not isinstance(ci_config, dict):
                        return {'error': 'Invalid YAML: not a mapping'}
                    return self._parse_yaml_ci(content, filename)
                except yaml.YAMLError as e:
                    return {'error': f'Invalid YAML: {str(e)}'}
            
            return {'error': f'Unsupported CI config: {filename}'}
        except Exception as e:
            logger.error(f"Error parsing CI config {self.current_file}: {e}")
            return {'error': str(e)}

    def _parse_jenkinsfile(self, content: str) -> Dict[str, Any]:
        """Parse Jenkins pipeline syntax"""
        result = {
            'stages': [],
            'environment': {},
            'agents': [],
            'post_actions': []
        }
        
        current_stage = None
        in_environment = False
        
        for line in content.splitlines():
            line = line.strip()
            
            if not line or line.startswith('//'):
                continue
                
            if line.startswith('stage('):
                if current_stage and current_stage['steps']:
                    result['stages'].append(current_stage)
                current_stage = {
                    'name': line.split('(')[1].split(')')[0].strip("'\""),
                    'steps': []
                }
            elif line.startswith('environment {'):
                in_environment = True
            elif line == '}':
                in_environment = False
            elif in_environment and '=' in line:
                key, value = line.split('=', 1)
                result['environment'][key.strip()] = value.strip().strip("'\"")
            elif current_stage and line.startswith(('sh ', 'bat ', 'pwsh ')):
                current_stage['steps'].append(line)
                
        if current_stage and current_stage['steps']:
            result['stages'].append(current_stage)
            
        return result

    def _parse_github_actions(self, content: str) -> Dict[str, Any]:
        """Parse GitHub Actions workflow"""
        try:
            workflow = yaml.safe_load(content)
            
            # Extract key components with semantic understanding
            result = {
                'name': workflow.get('name', ''),
                'triggers': self._extract_github_triggers(workflow),
                'jobs': self._extract_github_jobs(workflow),
                'env': workflow.get('env', {}),
                'permissions': workflow.get('permissions', {})
            }
            
            return result
        except yaml.YAMLError as e:
            return {'error': f'Invalid YAML: {str(e)}'}

    def _extract_github_triggers(self, workflow: Dict) -> Dict[str, Any]:
        """Extract and categorize GitHub Actions triggers"""
        triggers = {}
        on = workflow.get('on', {})
        
        if isinstance(on, str):
            triggers[on] = {}
        elif isinstance(on, dict):
            triggers = on
            
        return triggers

    def _extract_github_jobs(self, workflow: Dict) -> List[Dict[str, Any]]:
        """Extract and structure GitHub Actions jobs"""
        jobs = []
        for job_id, job_data in workflow.get('jobs', {}).items():
            jobs.append({
                'id': job_id,
                'name': job_data.get('name', job_id),
                'runs_on': job_data.get('runs-on', ''),
                'steps': job_data.get('steps', []),
                'needs': job_data.get('needs', []),
                'if': job_data.get('if', '')
            })
        return jobs

    def _parse_yaml_ci(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse YAML-based CI configs (GitLab, Travis, CircleCI)"""
        try:
            ci_config = yaml.safe_load(content)
            
            if 'gitlab-ci' in filename:
                return self._parse_gitlab_ci(ci_config)
            elif 'travis' in filename:
                return self._parse_travis_ci(ci_config)
            elif 'circleci' in filename:
                return self._parse_circle_ci(ci_config)
            elif 'azure-pipelines' in filename:
                return self._parse_azure_pipelines(ci_config)
                
            return {'error': 'Unknown CI system'}
        except yaml.YAMLError as e:
            return {'error': f'Invalid YAML: {str(e)}'}

    def _parse_gitlab_ci(self, config: Dict) -> Dict[str, Any]:
        """Parse GitLab CI specific structure"""
        return {
            'stages': config.get('stages', []),
            'variables': config.get('variables', {}),
            'jobs': {
                name: self._extract_gitlab_job(job_data)
                for name, job_data in config.items()
                if isinstance(job_data, dict) and 'stage' in job_data
            }
        }

    def _extract_gitlab_job(self, job_data: Dict) -> Dict[str, Any]:
        """Extract GitLab CI job information"""
        return {
            'stage': job_data.get('stage', ''),
            'script': job_data.get('script', []),
            'before_script': job_data.get('before_script', []),
            'after_script': job_data.get('after_script', []),
            'tags': job_data.get('tags', []),
            'only': job_data.get('only', []),
            'except': job_data.get('except', [])
        }

    def _parse_travis_ci(self, config: Dict) -> Dict[str, Any]:
        """Parse Travis CI configuration"""
        return {
            'language': config.get('language'),
            'os': config.get('os', []),
            'dist': config.get('dist'),
            'before_install': config.get('before_install', []),
            'install': config.get('install', []),
            'before_script': config.get('before_script', []),
            'script': config.get('script', []),
            'after_success': config.get('after_success', []),
            'after_failure': config.get('after_failure', []),
            'env': self._parse_travis_env(config.get('env', {})),
            'matrix': config.get('matrix', {}),
            'cache': config.get('cache', {})
        }

    def _parse_travis_env(self, env_config: Any) -> Dict[str, Any]:
        """Parse Travis CI environment configuration"""
        if isinstance(env_config, list):
            return {'matrix': env_config}
        elif isinstance(env_config, dict):
            return env_config
        return {'global': [], 'matrix': []}

    def _parse_circle_ci(self, config: Dict) -> Dict[str, Any]:
        """Parse CircleCI configuration"""
        return {
            'version': config.get('version'),
            'orbs': config.get('orbs', {}),
            'jobs': self._parse_circle_jobs(config.get('jobs', {})),
            'workflows': config.get('workflows', {}),
            'executors': config.get('executors', {})
        }

    def _parse_circle_jobs(self, jobs: Dict) -> Dict[str, Any]:
        """Parse CircleCI jobs configuration"""
        parsed_jobs = {}
        for job_name, job_config in jobs.items():
            parsed_jobs[job_name] = {
                'docker': job_config.get('docker', []),
                'steps': job_config.get('steps', []),
                'environment': job_config.get('environment', {}),
                'working_directory': job_config.get('working_directory'),
                'parallelism': job_config.get('parallelism', 1)
            }
        return parsed_jobs

    def _parse_azure_pipelines(self, config: Dict) -> Dict[str, Any]:
        """Parse Azure Pipelines configuration"""
        return {
            'trigger': config.get('trigger', []),
            'pool': config.get('pool', {}),
            'variables': config.get('variables', {}),
            'stages': self._parse_azure_stages(config.get('stages', [])),
            'jobs': self._parse_azure_jobs(config.get('jobs', [])),
            'steps': config.get('steps', [])
        }

    def _parse_azure_stages(self, stages: List[Dict]) -> List[Dict[str, Any]]:
        """Parse Azure Pipelines stages"""
        return [{
            'stage': stage.get('stage', ''),
            'displayName': stage.get('displayName', ''),
            'jobs': self._parse_azure_jobs(stage.get('jobs', [])),
            'condition': stage.get('condition', '')
        } for stage in stages]

    def _parse_azure_jobs(self, jobs: List[Dict]) -> List[Dict[str, Any]]:
        """Parse Azure Pipelines jobs"""
        return [{
            'job': job.get('job', ''),
            'displayName': job.get('displayName', ''),
            'pool': job.get('pool', {}),
            'steps': job.get('steps', []),
            'condition': job.get('condition', '')
        } for job in jobs]

class ProjectConfigParser(BaseFileParser):
    """Parser for project configuration and metadata"""
    def supported_extensions(self) -> List[str]:
        return [
            '.gitignore',  # Git ignore rules
            '.dockerignore',  # Docker ignore rules
            '.editorconfig',  # Editor configuration
            'tox.ini',  # Python test configuration
            '.eslintrc',  # JavaScript linting
            '.prettierrc',  # Code formatting
            'sonar-project.properties',  # SonarQube config
            '.coveragerc',  # Coverage config
            'pytest.ini',  # Pytest config
            'phpunit.xml'  # PHPUnit config
        ]

    def parse(self, content: str) -> Dict[str, Any]:
        """Parse project configuration files"""
        if not content.strip():
            return {'error': 'Empty file'}
        
        try:
            filename = Path(self.current_file).name.lower()
            
            if filename in ['.gitignore', '.dockerignore']:
                return self._parse_ignore_file(content)
            elif filename == '.editorconfig':
                return self._parse_editorconfig(content)
            elif filename.endswith('.properties'):
                return self._parse_properties(content)
            elif filename.endswith('.xml'):
                try:
                    root = ET.fromstring(content)
                    return self._xml_to_dict(root)
                except ET.ParseError as e:
                    return {'error': f'Invalid XML: {str(e)}'}
            elif filename.endswith('.ini'):
                return self._parse_ini(content)
            
            return {'error': f'Unsupported config file: {filename}'}
        except Exception as e:
            logger.error(f"Error parsing config file {self.current_file}: {e}")
            return {'error': str(e)}

    def _parse_ignore_file(self, content: str) -> Dict[str, Any]:
        """Parse .gitignore or .dockerignore files"""
        patterns = {
            'include': [],
            'exclude': [],
            'comments': []
        }
        
        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('#'):
                patterns['comments'].append(line[1:].strip())
            elif line.startswith('!'):
                patterns['include'].append(line[1:])
            else:
                patterns['exclude'].append(line)
                
        return patterns

    def _parse_editorconfig(self, content: str) -> Dict[str, Any]:
        """Parse .editorconfig file"""
        config = {}
        current_section = None
        
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            if line.startswith('[') and line.endswith(']'):
                current_section = line[1:-1]
                config[current_section] = {}
            elif current_section and '=' in line:
                key, value = line.split('=', 1)
                config[current_section][key.strip()] = value.strip()
                
        return config

    def _parse_properties(self, content: str) -> Dict[str, Any]:
        """Parse .properties files"""
        try:
            if PROPERTIES_PARSER == "jproperties":
                props = Properties()
                props.load(content)
                return {key: value.data for key, value in props.items()}
            elif PROPERTIES_PARSER == "javaproperties":
                return dict(javaproperties.loads(content))
            else:
                # Fallback to basic properties parsing
                properties = {}
                for line in content.splitlines():
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            properties[key.strip()] = value.strip()
                return properties
        except Exception as e:
            logger.error(f"Error parsing properties file: {e}")
            return {"error": str(e)}

    def _parse_xml_config(self, content: str) -> Dict[str, Any]:
        """Parse XML configuration files"""
        try:
            root = ET.fromstring(content)
            return self._xml_to_dict(root)
        except ET.ParseError as e:
            return {'error': f'Invalid XML: {str(e)}'}

    def _xml_to_dict(self, element: ET.Element) -> Dict[str, Any]:
        """Convert XML element to dictionary"""
        result = {}
        
        # Handle attributes
        if element.attrib:
            result['@attributes'] = dict(element.attrib)
            
        # Handle child elements
        for child in element:
            child_data = self._xml_to_dict(child)
            if child.tag in result:
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_data)
            else:
                result[child.tag] = child_data
                
        # Handle text content
        if element.text and element.text.strip():
            if result:
                result['#text'] = element.text.strip()
            else:
                result = element.text.strip()
                
        return result

    def _parse_ini(self, content: str) -> Dict[str, Any]:
        """Parse INI-style configuration files"""
        config = {}
        current_section = 'default'
        
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            if line.startswith('[') and line.endswith(']'):
                current_section = line[1:-1]
                config[current_section] = {}
            elif '=' in line:
                key, value = line.split('=', 1)
                section = config.get(current_section, {})
                section[key.strip()] = value.strip()
                config[current_section] = section
                
        return {'config': config}

class LicenseParser(BaseFileParser):
    """Parser for license and legal files"""
    def supported_extensions(self) -> List[str]:
        return [
            'LICENSE',
            'LICENSE.txt',
            'LICENSE.md',
            'COPYING',
            'NOTICE'
        ]

    def parse(self, content: str) -> Dict[str, Any]:
        """Parse license and legal files with semantic understanding"""
        if not content.strip():
            return {'error': 'Empty file'}
        
        try:
            # Basic validation that this looks like a license
            content_lower = content.lower()
            license_indicators = [
                'license', 'copyright', 'permission', 'rights',
                'permitted', 'restricted', 'conditions', 'warranty'
            ]
            
            # Check if content has any license-like terms
            if not any(indicator in content_lower for indicator in license_indicators):
                return {'error': 'Not a valid license file'}
            
            # Split into sections based on blank lines
            sections = [s.strip() for s in re.split(r'\n\s*\n', content) if s.strip()]
            
            result = {
                'type': self._identify_license_type(content),
                'sections': {
                    'header': sections[0] if sections else '',
                    'body': sections[1:-1] if len(sections) > 2 else [],
                    'footer': sections[-1] if len(sections) > 1 else ''
                },
                'metadata': self._extract_license_metadata(content),
                'restrictions': self._extract_restrictions(content),
                'permissions': self._extract_permissions(content)
            }
            
            return result
        except Exception as e:
            logger.error(f"Error parsing license file: {e}")
            return {'error': str(e)}

    def _identify_license_type(self, content: str) -> str:
        """Identify the type of license based on content"""
        content_lower = content.lower()
        
        license_patterns = {
            'mit': r'mit license|permission is hereby granted, free of charge',
            'apache': r'apache license|licensed under the apache license',
            'gpl': r'gnu general public license|gpl',
            'bsd': r'bsd license|redistribution and use in source and binary forms',
            'isc': r'isc license|permission to use, copy, modify, and/or distribute',
            'mpl': r'mozilla public license',
            'unlicense': r'this is free and unencumbered software'
        }
        
        for license_type, pattern in license_patterns.items():
            if re.search(pattern, content_lower):
                return license_type.upper()
                
        return 'UNKNOWN'

    def _extract_license_metadata(self, content: str) -> Dict[str, str]:
        """Extract metadata from license content"""
        metadata = {}
        
        # Try to find copyright year and holder
        copyright_match = re.search(
            r'copyright\s+(?:\(c\)\s*)?(\d{4}(?:-\d{4})?)\s*(.+?)(?:\n|$)', 
            content,
            re.IGNORECASE
        )
        if copyright_match:
            metadata['copyright_year'] = copyright_match.group(1)
            metadata['copyright_holder'] = copyright_match.group(2).strip()
            
        # Try to find version information
        version_match = re.search(r'version\s+([\d.]+)', content.lower())
        if version_match:
            metadata['version'] = version_match.group(1)
            
        return metadata

    def _extract_restrictions(self, content: str) -> List[str]:
        """Extract usage restrictions from license"""
        content_lower = content.lower()
        restrictions = []
        
        restriction_patterns = [
            (r'not.*sublicense', 'No sublicensing'),
            (r'not.*modify', 'No modification'),
            (r'not.*commercial', 'No commercial use'),
            (r'not.*distribute', 'No distribution'),
            (r'warranty.*disclaimed', 'No warranty'),
            (r'liability.*limited', 'Limited liability')
        ]
        
        for pattern, restriction in restriction_patterns:
            if re.search(pattern, content_lower):
                restrictions.append(restriction)
                
        return restrictions

    def _extract_permissions(self, content: str) -> List[str]:
        """Extract permitted actions from license"""
        content_lower = content.lower()
        permissions = []
        
        permission_patterns = [
            (r'permission.*modify', 'Can modify'),
            (r'permission.*merge', 'Can merge'),
            (r'permission.*publish', 'Can publish'),
            (r'permission.*distribute', 'Can distribute'),
            (r'permission.*sublicense', 'Can sublicense'),
            (r'permission.*sell', 'Can sell'),
            (r'permission.*private use', 'Private use allowed')
        ]
        
        for pattern, permission in permission_patterns:
            if re.search(pattern, content_lower):
                permissions.append(permission)
                
        return permissions

class MetadataParser(BaseFileParser):
    """Parser for repository metadata files"""
    def supported_extensions(self) -> List[str]:
        return [
            'AUTHORS',
            'CHANGELOG',
            'CONTRIBUTING',
            'PATENTS',
            'VERSION'
        ]

    def parse(self, content: str) -> Dict[str, Any]:
        """Parse repository metadata files"""
        return {
            'content': content,
            'type': Path(self.current_file).name.lower(),
            'sections': self._parse_sections(content)
        }

    def _parse_sections(self, content: str) -> List[Dict[str, str]]:
        """Parse content into sections based on headers"""
        sections = []
        current_section = None
        
        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
            
            if line.isupper() and not line.startswith(' '):
                if current_section:
                    current_section['content'] = [c.strip() for c in current_section['content']]
                    sections.append(current_section)
                current_section = {'title': line, 'content': []}
            elif current_section:
                current_section['content'].append(line)
        
        if current_section and current_section['content']:
            current_section['content'] = [c.strip() for c in current_section['content']]
            sections.append(current_section)
        
        return sections

def initialize_parsers() -> CustomParserRegistry:
    """Initialize and register all custom parsers"""
    registry = CustomParserRegistry()
    
    registry.register_parser(ConfigParser())  # For .ini/.conf files
    registry.register_parser(DocContentParser())  # For semantic doc content
    registry.register_parser(BuildSystemParser())  # For build/package files
    registry.register_parser(CIConfigParser())  # For CI/CD configs
    registry.register_parser(ProjectConfigParser())  # For project metadata
    registry.register_parser(LicenseParser())  # For license files
    registry.register_parser(MetadataParser())  # For repository metadata
    
    return registry