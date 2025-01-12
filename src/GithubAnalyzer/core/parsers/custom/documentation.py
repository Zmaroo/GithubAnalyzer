"""Documentation parser for markdown and other documentation files"""
from typing import List, Dict, Any, Optional
from pathlib import Path
from ..base import BaseParser
from ...models.base import ParseResult

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
        try:
            if not content.strip():
                return ParseResult(
                    success=False,
                    errors=["Empty content"]
                )
            
            sections = self._parse_sections(content)
            
            return ParseResult(
                success=True,
                semantic={
                    'type': 'documentation',
                    'sections': sections
                }
            )
            
        except Exception as e:
            return ParseResult(
                success=False,
                errors=[f"Documentation parse error: {str(e)}"]
            )
    
    def _parse_sections(self, content: str) -> List[Dict[str, Any]]:
        """Parse content into sections"""
        sections = []
        current_section = None
        current_content = []
        
        for line in content.split('\n'):
            if line.startswith('#'):
                # Save previous section if exists
                if current_section:
                    sections.append({
                        'title': current_section,
                        'content': '\n'.join(current_content).strip()
                    })
                # Start new section
                current_section = line.lstrip('#').strip()
                current_content = []
            else:
                current_content.append(line)
        
        # Add last section
        if current_section:
            sections.append({
                'title': current_section,
                'content': '\n'.join(current_content).strip()
            })
        
        return sections 