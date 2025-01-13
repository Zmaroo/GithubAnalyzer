"""Documentation parser for markdown and other documentation files"""
from typing import Dict, Any, List
from pathlib import Path
from ..base import BaseParser
from ...models import ParseResult

class DocumentationParser(BaseParser):
    """Parser for documentation files"""
    
    def __init__(self):
        super().__init__()
        self.supported_extensions = {'.md', '.rst', '.txt'}
    
    def can_parse(self, file_path: str) -> bool:
        """Check if file can be parsed"""
        return Path(file_path).suffix.lower() in self.supported_extensions
    
    def parse(self, content: str) -> ParseResult:
        """Parse documentation content"""
        if not content.strip():
            return ParseResult(
                ast=None,
                semantic={},
                errors=["Empty content"],
                success=False
            )
            
        try:
            sections = self._parse_sections(content)
            return ParseResult(
                ast=sections,
                semantic={
                    'type': 'documentation',
                    'sections': [
                        {
                            'title': title,
                            'content': content
                        }
                        for title, content in sections.items()
                    ]
                },
                success=True
            )
        except Exception as e:
            return ParseResult(
                ast=None,
                semantic={},
                errors=[str(e)],
                success=False
            )
    
    def _parse_sections(self, content: str) -> Dict[str, str]:
        """Parse content into sections"""
        sections = {}
        current_section = None
        current_content = []
        
        for line in content.split('\n'):
            if line.startswith('#'):
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = line.lstrip('#').strip()
                current_content = []
            else:
                current_content.append(line)
                
        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()
            
        return sections 