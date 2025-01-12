from pathlib import Path
from typing import List
from ..base import BaseParser
from ...models.base import ParseResult
from ...models.code import DocumentationInfo
from ...utils.logging import setup_logger

logger = setup_logger(__name__)

class DocumentationParser(BaseParser):
    """Parser for documentation files"""
    
    def can_parse(self, file_path: str) -> bool:
        """Check if file is a documentation file"""
        path = Path(file_path)
        return path.suffix in {'.md', '.rst', '.txt'} or \
               path.name.upper() in {'README', 'CHANGELOG', 'CONTRIBUTING'}

    def parse(self, content: str) -> ParseResult:
        """Parse documentation content"""
        try:
            path = Path(self.current_file)
            doc_type = 'markdown' if path.suffix == '.md' else \
                      'rst' if path.suffix == '.rst' else 'text'
            
            sections = self._parse_sections(content)
            
            return ParseResult(
                ast=None,
                semantic={
                    'type': 'documentation',
                    'format': doc_type,
                    'sections': sections,
                    'content': content
                },
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error parsing documentation {self.current_file}: {e}")
            return ParseResult(
                ast=None,
                semantic={},
                errors=[str(e)],
                success=False
            )

    def _parse_sections(self, content: str) -> List[Dict[str, Any]]:
        """Parse document sections"""
        sections = []
        current_section = None
        current_content = []
        
        for line in content.splitlines():
            if line.startswith('#'):  # Markdown heading
                if current_section:
                    sections.append({
                        'title': current_section,
                        'content': '\n'.join(current_content)
                    })
                current_section = line.lstrip('#').strip()
                current_content = []
            else:
                current_content.append(line)
                
        # Add last section
        if current_section:
            sections.append({
                'title': current_section,
                'content': '\n'.join(current_content)
            })
            
        return sections 