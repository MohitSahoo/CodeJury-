"""
Multi-language security parsers.
"""

from parsers.base_parser import LanguageParser, ParserFactory

# Import all parsers to register them
from parsers.python_parser import PythonParser
from parsers.javascript_parser import JavaScriptParser
from parsers.java_parser import JavaParser
from parsers.go_parser import GoParser

__all__ = [
    'LanguageParser',
    'ParserFactory',
    'PythonParser',
    'JavaScriptParser',
    'JavaParser',
    'GoParser',
]
