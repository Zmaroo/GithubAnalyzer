from tree_sitter import Parser
from tree_sitter_language_pack import get_binding, get_language, get_parser
from pathlib import Path
import json

def main():
    # Get the parser
    parser = get_parser('solidity')

    # Sample Solidity code
    code = """
    // SPDX-License-Identifier: MIT
    pragma solidity ^0.8.0;

    contract SimpleStorage {
        uint256 private value;

        constructor(uint256 initialValue) {
            value = initialValue;
        }

        function setValue(uint256 newValue) public {
            value = newValue;
        }

        function getValue() public view returns (uint256) {
            return value;
        }

        modifier onlyPositive(uint256 _value) {
            require(_value > 0, "Value must be positive");
            _;
        }

        function setValueWithCheck(uint256 newValue) public onlyPositive(newValue) {
            value = newValue;
        }
    }
    """

    # Parse the code
    tree = parser.parse(bytes(code, "utf8"))

    # Convert to JSON
    def node_to_dict(node):
        result = {
            "type": node.type,
            "text": code[node.start_byte:node.end_byte],
            "start_point": node.start_point,
            "end_point": node.end_point,
            "children": [node_to_dict(child) for child in node.children]
        }
        
        # Add field information if available
        if len(node.children) > 0 and hasattr(node, 'fields'):
            fields = {}
            for field_name, field_value in node.fields.items():
                if isinstance(field_value, list):
                    fields[field_name] = [child.type for child in field_value]
                else:
                    fields[field_name] = field_value.type if field_value else None
            if fields:
                result["fields"] = fields
                
        return result

    ast = node_to_dict(tree.root_node)

    # Write to file
    output_path = Path('solidity-node-types.json')
    with open(output_path, 'w') as f:
        json.dump(ast, f, indent=2)

if __name__ == "__main__":
    main() 