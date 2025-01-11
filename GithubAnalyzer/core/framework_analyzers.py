from typing import Dict, Any, List
import ast
from .code_parser import CodeParser
from .utils import setup_logger

logger = setup_logger(__name__)

class PydanticAnalyzer:
    def __init__(self):
        self.models = []
        self.validators = []
        self.configs = []
        self.code_parser = CodeParser()

    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        parse_result = self.code_parser.parse_file(file_path)
        if "error" in parse_result:
            return {}
            
        # Use semantic information from parse_result
        semantic = parse_result["semantic"]
        
        # Extract models, validators, etc.
        for cls in semantic["classes"]:
            if self._is_pydantic_model(cls):
                self.models.append(self._analyze_model(cls))
                
        return {
            'models': self.models,
            'validators': self.validators,
            'configs': self.configs
        }

    def analyze_tree(self, tree: ast.AST) -> Dict[str, Any]:
        results = {
            'models': [],
            'validators': [],
            'configs': []
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Check for Pydantic model inheritance
                if any(base.id == 'BaseModel' for base in node.bases 
                      if isinstance(base, ast.Name)):
                    results['models'].append(self._analyze_model(node))
                    
        return results

    def _analyze_model(self, node: ast.ClassDef) -> Dict[str, Any]:
        model_info = {
            'name': node.name,
            'fields': [],
            'validators': [],
            'config': None
        }
        
        for item in node.body:
            if isinstance(item, ast.AnnAssign):
                model_info['fields'].append(self._analyze_field(item))
            elif isinstance(item, ast.FunctionDef):
                if item.name.startswith('validate_'):
                    model_info['validators'].append(self._analyze_validator(item))
                    
        return model_info

    def _analyze_field(self, node: ast.AnnAssign) -> Dict[str, Any]:
        return {
            'name': node.target.id if isinstance(node.target, ast.Name) else None,
            'type': self._get_type_annotation(node.annotation)
        }

    def _analyze_validator(self, node: ast.FunctionDef) -> Dict[str, Any]:
        return {
            'name': node.name,
            'field': node.name.replace('validate_', '')
        }

    def _get_type_annotation(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Subscript):
            return f"{self._get_type_annotation(node.value)}[...]"
        return "unknown" 