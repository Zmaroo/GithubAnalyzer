from typing import Dict, Any, List
import re

class DocumentationAnalyzer:
    def __init__(self, nlp_model=None):
        self.nlp_model = nlp_model
        self.code_pattern = re.compile(r'```[\s\S]*?```')
        
    def analyze(self, content: str) -> Dict[str, Any]:
        sections = self._split_sections(content)
        return {
            'examples': self._extract_examples(content),
            'api_specs': self._extract_api_specs(sections),
            'configuration': self._extract_configuration(sections),
            'usage': self._extract_usage(sections)
        }

    def _split_sections(self, content: str) -> List[str]:
        # Split content into logical sections based on headers
        return re.split(r'\n#{1,6}\s', content)

    def _extract_examples(self, content: str) -> List[str]:
        # Extract code examples from markdown code blocks
        examples = []
        for match in self.code_pattern.finditer(content):
            example = match.group(0).strip('`').strip()
            if example:
                examples.append(example)
        return examples

    def _extract_api_specs(self, sections: List[str]) -> List[Dict[str, Any]]:
        specs = []
        for section in sections:
            if any(keyword in section.lower() 
                  for keyword in ['api', 'endpoint', 'method', 'function']):
                specs.append(self._parse_api_section(section))
        return specs

    def _extract_configuration(self, sections: List[str]) -> Dict[str, Any]:
        config = {}
        for section in sections:
            if any(keyword in section.lower() 
                  for keyword in ['config', 'configuration', 'settings']):
                config.update(self._parse_config_section(section))
        return config

    def _extract_usage(self, sections: List[str]) -> List[str]:
        usage = []
        for section in sections:
            if any(keyword in section.lower() 
                  for keyword in ['usage', 'example', 'how to']):
                usage.append(section.strip())
        return usage

    def _parse_api_section(self, section: str) -> Dict[str, Any]:
        # Parse API documentation section
        return {
            'description': section.split('\n')[0],
            'parameters': self._extract_parameters(section),
            'returns': self._extract_returns(section)
        }

    def _parse_config_section(self, section: str) -> Dict[str, Any]:
        # Parse configuration documentation section
        config = {}
        lines = section.split('\n')
        current_key = None
        
        for line in lines:
            if line.strip().startswith('- '):
                key_value = line.strip('- ').split(':', 1)
                if len(key_value) == 2:
                    config[key_value[0].strip()] = key_value[1].strip()
                    
        return config

    def _extract_parameters(self, section: str) -> List[Dict[str, str]]:
        params = []
        param_section = re.search(r'Parameters:?([\s\S]*?)(?:Returns:|$)', section)
        if param_section:
            param_lines = param_section.group(1).strip().split('\n')
            for line in param_lines:
                if line.strip().startswith('- '):
                    param_info = line.strip('- ').split(':', 1)
                    if len(param_info) == 2:
                        params.append({
                            'name': param_info[0].strip(),
                            'description': param_info[1].strip()
                        })
        return params

    def _extract_returns(self, section: str) -> Dict[str, str]:
        returns_section = re.search(r'Returns:?([\s\S]*?)(?:$)', section)
        if returns_section:
            return {'description': returns_section.group(1).strip()}
        return {} 