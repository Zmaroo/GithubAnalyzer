from tree_sitter_language_pack import get_binding, get_language, get_parser

def test_language(name):
    print(f"\nTesting {name}:")
    try:
        binding = get_binding(name)
        lang = get_language(name)
        parser = get_parser(name)
        print(f"{name} support: OK")
    except Exception as e:
        print(f"{name} error: {str(e)}")

# Test each language
test_language('tcl')
test_language('commonlisp')
test_language('ada')
test_language('elixir')
test_language('erlang') 