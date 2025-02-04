from tree_sitter import Parser
from tree_sitter_language_pack import get_binding, get_language, get_parser
from pathlib import Path
import json

def main():
    # Get the parser
    parser = get_parser('verilog')

    # Sample Verilog code
    code = """
    module counter(
        input wire clk,
        input wire rst,
        output reg [3:0] count
    );
        always @(posedge clk or posedge rst) begin
            if (rst)
                count <= 4'b0000;
            else
                count <= count + 1;
        end
    endmodule

    module test_module;
        function automatic [7:0] add;
            input [7:0] a, b;
            begin
                add = a + b;
            end
        endfunction

        task automatic print_value;
            input [7:0] value;
            begin
                $display("Value: %h", value);
            end
        endtask
    endmodule
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
    output_path = Path('verilog-node-types.json')
    with open(output_path, 'w') as f:
        json.dump(ast, f, indent=2)

if __name__ == "__main__":
    main() 