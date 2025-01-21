def test_cache_service_integration():
    """Test cache service integration with other components"""
    from src.GithubAnalyzer.common.services.cache_service import CacheService
    from src.GithubAnalyzer.core.services.parser_service import ParserService
    from src.GithubAnalyzer.core.services.file_service import FileService
    from src.GithubAnalyzer.analysis.services.parsers.tree_sitter import TreeSitterParser
    
    # Test cache service works with all dependent services
    cache_service = CacheService()
    parser_service = ParserService(cache_service)
    file_service = FileService(cache_service)
    tree_sitter_parser = TreeSitterParser(cache_service)

def test_parser_registry_integration():
    """Test parser registry integration"""
    from src.GithubAnalyzer.analysis.services.parser_registry import ParserRegistry
    from src.GithubAnalyzer.core.services.parser_service import ParserService
    from src.GithubAnalyzer.analysis.services.parsers.tree_sitter import TreeSitterParser
    from src.GithubAnalyzer.analysis.services.parsers.documentation import DocumentationParser
    from src.GithubAnalyzer.analysis.services.parsers.license import LicenseParser
    
    registry = ParserRegistry()
    
    # Register different parser types
    tree_sitter = TreeSitterParser()
    doc_parser = DocumentationParser()
    license_parser = LicenseParser()
    
    registry.register("tree-sitter", tree_sitter)
    registry.register("documentation", doc_parser)
    registry.register("license", license_parser)
    
    # Verify parsers are properly registered
    assert registry.get_parser("tree-sitter") == tree_sitter
    assert registry.get_parser("documentation") == doc_parser
    assert registry.get_parser("license") == license_parser 