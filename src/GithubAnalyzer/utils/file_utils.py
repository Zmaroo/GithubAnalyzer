"""File system utilities"""
from typing import Iterator, List, Set
from pathlib import Path
import os
from ...config.settings import settings

class FileDiscovery:
    """File discovery and filtering utility"""
    
    def discover_files_batched(
        self, 
        root_path: str, 
        batch_size: int = settings.BATCH_SIZE
    ) -> Iterator[List[str]]:
        """Discover files in batches for memory efficiency"""
        batch = []
        
        for root, _, filenames in os.walk(root_path):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                path = Path(file_path)
                
                if (
                    path.suffix in settings.SUPPORTED_EXTENSIONS and
                    not any(p in path.parts for p in settings.EXCLUDE_PATTERNS) and
                    path.stat().st_size <= settings.MAX_FILE_SIZE
                ):
                    batch.append(file_path)
                    
                    if len(batch) >= batch_size:
                        yield batch
                        batch = []
                        
        if batch:
            yield batch 