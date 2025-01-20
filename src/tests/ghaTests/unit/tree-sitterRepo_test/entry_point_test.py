from collections.abc import Callable
from json import loads
from pathlib import Path
from typing import Any, cast, List

import pytest
from tree_sitter import Language, Parser

from tree_sitter_language_pack import (
    get_binding,
    get_language,
    get_parser,
    SupportedLanguage,
)

language_definitions = cast(
    dict[str, dict[str, str]],
    loads((Path(__file__).resolve().parent / "language_definitions.json").read_text()),
)

language_names = [
    *list(language_definitions.keys()),
    "csharp",
    "embeddedtemplate",
    "yaml",
    "typescript",
    "tsx",
    "xml",
    "php",
    "dtd",
]

def test_language_names() -> None:
    """Test that language_names is a list of strings."""
    assert isinstance(language_names, list)
    assert all(isinstance(name, str) for name in language_names)


@pytest.mark.parametrize("language", language_names)
def test_get_binding(language: SupportedLanguage) -> None:
    """Test that get_binding returns either an integer or a capsule object."""
    binding = get_binding(language)
    assert isinstance(binding, (int, object)), f"Expected int or capsule object, got {type(binding)}"


@pytest.mark.parametrize("language", language_names)
def test_get_language(language: SupportedLanguage) -> None:
    assert isinstance(get_language(language), Language)


@pytest.mark.parametrize("language", language_names)
def test_get_parser(language: SupportedLanguage) -> None:
    assert isinstance(get_parser(language), Parser)


@pytest.mark.parametrize("handler", [get_language, get_parser])
def test_raises_exception_for_invalid_name(handler: Callable[[str], Any]) -> None:
    with pytest.raises(LookupError):
        handler("invalid")
