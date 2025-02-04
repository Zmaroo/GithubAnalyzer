from tree_sitter_language_pack import get_binding, get_language, get_parser
from pathlib import Path
from src.GithubAnalyzer.services.analysis.parsers.query_patterns import QUERY_PATTERNS

parser = get_parser('fish')
lang = get_language('fish')
pattern = QUERY_PATTERNS['fish']['function']

with open('tests/data/sample.fish', 'r') as f:
    source = f.read()
tree = parser.parse(bytes(source, 'utf8'))
query = lang.query(pattern)
matches = query.matches(tree.root_node)
print(f'Found {len(matches)} matches')
for match in matches[:2]:
    for capture_name, node in match[1].items():
        text = node.text.decode('utf8')
        print(f'{capture_name}: {text[:100]}...') 