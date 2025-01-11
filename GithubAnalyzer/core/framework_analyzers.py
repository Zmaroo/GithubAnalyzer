from typing import Dict, Any, List
import ast

class PydanticAnalyzer:
    def __init__(self):
        self.models = []
        self.validators = []
        self.configs = []

    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        with open(file_path) as f:
            tree = ast.parse(f.read())
            return self.analyze_tree(tree)

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