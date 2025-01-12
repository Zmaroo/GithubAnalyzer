from pathlib import Path
from typing import Dict, Any, Optional
from ..base import BaseParser
from ...models.base import ParseResult
from ...utils.logging import setup_logger

logger = setup_logger(__name__)

class LicenseParser(BaseParser):
    """Parser for software license files"""
    
    # Common license identifiers
    LICENSE_PATTERNS = {
        'MIT': ['MIT License', 'Permission is hereby granted, free of charge'],
        'Apache-2.0': ['Apache License', 'Version 2.0'],
        'GPL-3.0': ['GNU GENERAL PUBLIC LICENSE', 'Version 3'],
        'GPL-2.0': ['GNU GENERAL PUBLIC LICENSE', 'Version 2'],
        'BSD': ['BSD License', 'Redistribution and use in source and binary forms'],
        'ISC': ['ISC License', 'Permission to use, copy, modify, and/or distribute'],
        'LGPL': ['GNU LESSER GENERAL PUBLIC LICENSE'],
        'MPL': ['Mozilla Public License'],
        'Unlicense': ['This is free and unencumbered software']
    }
    
    def can_parse(self, file_path: str) -> bool:
        """Check if file is a license file"""
        path = Path(file_path)
        return path.name.upper() in {'LICENSE', 'COPYING', 'LICENSE.MD', 'LICENSE.TXT'}

    def parse(self, content: str) -> ParseResult:
        """Parse license content"""
        try:
            license_type = self._detect_license_type(content)
            
            return ParseResult(
                ast=None,
                semantic={
                    'type': 'license',
                    'license_type': license_type,
                    'content': content,
                    'summary': self._get_license_summary(license_type)
                },
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error parsing license {self.current_file}: {e}")
            return ParseResult(
                ast=None,
                semantic={},
                errors=[str(e)],
                success=False
            )

    def _detect_license_type(self, content: str) -> str:
        """Detect license type from content"""
        content_upper = content.upper()
        
        for license_type, patterns in self.LICENSE_PATTERNS.items():
            if all(pattern.upper() in content_upper for pattern in patterns):
                return license_type
                
        return 'Unknown'

    def _get_license_summary(self, license_type: str) -> Dict[str, Any]:
        """Get summary information for license type"""
        summaries = {
            'MIT': {
                'permissions': ['commercial-use', 'modifications', 'distribution', 'private-use'],
                'conditions': ['include-copyright'],
                'limitations': ['liability', 'warranty']
            },
            'Apache-2.0': {
                'permissions': ['commercial-use', 'modifications', 'distribution', 'patent-use', 'private-use'],
                'conditions': ['include-copyright', 'state-changes', 'include-notice'],
                'limitations': ['liability', 'warranty', 'trademark-use']
            },
            # Add other license summaries as needed
        }
        
        return summaries.get(license_type, {
            'permissions': [],
            'conditions': [],
            'limitations': []
        }) 