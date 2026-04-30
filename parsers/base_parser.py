"""
Language Parser Base Classes
Abstract interface for multi-language security parsing.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Set
from pathlib import Path


class LanguageParser(ABC):
    """Abstract base class for language-specific security parsers."""

    def __init__(self):
        self.security_patterns = self._define_security_patterns()

    @abstractmethod
    def _define_security_patterns(self) -> Dict[str, List[str]]:
        """Define language-specific security patterns."""
        pass

    @abstractmethod
    def parse_file(self, filepath: str, diff_content: str) -> Dict[str, Any]:
        """
        Parse file and extract security-relevant patterns.

        Args:
            filepath: Path to source file
            diff_content: Git diff for this file

        Returns:
            Dictionary with extracted security patterns
        """
        pass

    @abstractmethod
    def _find_tainted_variables(self, content: str) -> Set[str]:
        """Find variables assigned from user input sources."""
        pass

    @abstractmethod
    def _extract_functions(self, content: str) -> List[Dict[str, Any]]:
        """Extract function definitions."""
        pass

    @abstractmethod
    def _find_sql_patterns(self, content: str) -> List[Dict[str, Any]]:
        """Find potential SQL query construction."""
        pass

    @abstractmethod
    def _find_user_inputs(self, content: str) -> List[Dict[str, Any]]:
        """Find user input sources."""
        pass

    @abstractmethod
    def _find_file_operations(self, content: str, tainted_vars: Set[str]) -> List[Dict[str, Any]]:
        """Find file operations that could be vulnerable."""
        pass

    @abstractmethod
    def _find_subprocess_calls(self, content: str, tainted_vars: Set[str]) -> List[Dict[str, Any]]:
        """Find subprocess/system calls."""
        pass

    def get_file_extension(self) -> List[str]:
        """Return supported file extensions."""
        return []

    def _empty_extraction(self, filepath: str, error: str = "Could not read file") -> Dict[str, Any]:
        """Return empty extraction structure."""
        return {
            "filepath": filepath,
            "parseable": False,
            "error": error,
            "has_security_patterns": False
        }


class ParserFactory:
    """Factory for creating language-specific parsers."""

    _parsers: Dict[str, type] = {}

    @classmethod
    def register_parser(cls, extensions: List[str], parser_class: type):
        """Register a parser for specific file extensions."""
        for ext in extensions:
            cls._parsers[ext] = parser_class

    @classmethod
    def get_parser(cls, filepath: str) -> LanguageParser:
        """
        Get appropriate parser for a file.

        Args:
            filepath: Path to source file

        Returns:
            LanguageParser instance

        Raises:
            ValueError: If no parser found for file extension
        """
        ext = Path(filepath).suffix.lower()

        if ext not in cls._parsers:
            raise ValueError(f"No parser registered for extension: {ext}")

        parser_class = cls._parsers[ext]
        return parser_class()

    @classmethod
    def supports_file(cls, filepath: str) -> bool:
        """Check if a file type is supported."""
        ext = Path(filepath).suffix.lower()
        return ext in cls._parsers

    @classmethod
    def get_supported_extensions(cls) -> List[str]:
        """Get list of all supported file extensions."""
        return list(cls._parsers.keys())
