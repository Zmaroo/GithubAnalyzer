# This library exposes two functions get_language and get_parser.

from tree_sitter_language_pack import get_binding, get_language, get_parser

python_binding = get_binding('python')  # this is an int pointing to the C binding
python_lang = get_language('python')  # this is an instance of tree_sitter.Language
python_parser = get_parser('python')  # this is an instance of tree_sitter.Parser


# how to find all the strings being used as comments in python code?

# Start with some example Python code
example = """
#!shebang
# License blah blah (Apache 2.0)
"This is a module docstring."

a = 1

'''This
is
not
a
multiline
comment.'''

b = 2

class Test:
    "This is a class docstring."

    'This is bogus.'

    def test(self):
        "This is a function docstring."

        "Please, no."

        return 1

c = 3
"""

#Notice a couple things: Python has module, class, and function docstrings that bare a 
# striking resemblance to the phony string comments.
# Python supports single-quoted, double-quoted, triple-single-quoted, and triple-double-quoted 
# strings (not to mention prefixes for raw strings, unicode strings, and more).
# Creating a regular expression to capture the phony string comments would be exceedingly difficult!

# Enter tree-sitter

# Tre-sitter creates an abstract syntax tree (actually, a concrete syntax tree) and supports queries
# that can be used to find all the nodes that have the type 'comment'.

# tree-sitter creates an abstract syntax tree (actually, a concrete syntax tree) and supports 
# queries

tree = python_parser.parse(example.encode())
node = tree.root_node
print(node.sexp())

# Look for statements that are a single string expression

stmt_str_pattern = '(expression_statement (string)) @stmt_str'
stmt_str_query = python_lang.query(stmt_str_pattern)
stmt_strs = stmt_str_query.captures(node)
stmt_str_points = set(
    (node.start_point, node.end_point) for node, _ in stmt_strs
)
print(stmt_str_points)

# Now, find those statement string expressions that are actually module, class, 
# or function docstrings

doc_str_pattern = """
    (module . (comment)* . (expression_statement (string)) @module_doc_str)

    (class_definition
        body: (block . (expression_statement (string)) @class_doc_str))

    (function_definition
        body: (block . (expression_statement (string)) @function_doc_str))
"""
doc_str_query = python_lang.query(doc_str_pattern)
doc_strs = doc_str_query.captures(node)
doc_str_points = set(
    (node.start_point, node.end_point) for node, _ in doc_strs
)

# With the set of string expression statements and the set of docstring statements, 
# the locations of all phony string comments is...

comment_strs = stmt_str_points - doc_str_points
print(sorted(comment_strs))



