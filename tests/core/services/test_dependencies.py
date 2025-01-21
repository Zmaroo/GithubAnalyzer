def test_parser_inheritance():
    """Test parser inheritance relationships"""
    from src.GithubAnalyzer.core.services.parsers.base import BaseParser
    from src.GithubAnalyzer.core.services.parsers.config_parser import ConfigParser
    from src.GithubAnalyzer.analysis.services.parsers.tree_sitter import TreeSitterParser
    from src.GithubAnalyzer.analysis.services.parsers.documentation import DocumentationParser
    from src.GithubAnalyzer.analysis.services.parsers.license import LicenseParser
    
    assert issubclass(ConfigParser, BaseParser)
    assert issubclass(TreeSitterParser, BaseParser)
    assert issubclass(DocumentationParser, BaseParser)
    assert issubclass(LicenseParser, BaseParser)

def test_service_inheritance():
    """Test service inheritance relationships"""
    from src.GithubAnalyzer.core.services.base_service import BaseService
    from src.GithubAnalyzer.core.services.file_service import FileService
    from src.GithubAnalyzer.core.services.parser_service import ParserService
    
    assert issubclass(FileService, BaseService)
    assert issubclass(ParserService, BaseService) 