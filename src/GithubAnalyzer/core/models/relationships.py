"""Code relationship models"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Set, Optional

@dataclass
class CodeRelationship:
    """Represents a relationship between code components"""
    source: str
    target: str
    type: str
    properties: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CodeRelationships:
    """Collection of code relationships"""
    imports: List[CodeRelationship] = field(default_factory=list)
    calls: List[CodeRelationship] = field(default_factory=list)
    inherits: List[CodeRelationship] = field(default_factory=list)
    references: List[CodeRelationship] = field(default_factory=list)
    dependencies: Set[str] = field(default_factory=set)
    
    def add_import(self, source: str, target: str, **properties):
        """Add import relationship"""
        self.imports.append(CodeRelationship(source, target, "IMPORTS", properties))
        self.dependencies.add(target)
    
    def add_call(self, source: str, target: str, **properties):
        """Add function call relationship"""
        self.calls.append(CodeRelationship(source, target, "CALLS", properties))
    
    def add_inheritance(self, source: str, target: str, **properties):
        """Add inheritance relationship"""
        self.inherits.append(CodeRelationship(source, target, "INHERITS", properties))
        self.dependencies.add(target)
    
    def add_reference(self, source: str, target: str, **properties):
        """Add general reference relationship"""
        self.references.append(CodeRelationship(source, target, "REFERENCES", properties)) 