"""
Java Language Parser
Regex-based pattern matching for Java security analysis.
"""

import re
from typing import Dict, List, Any, Set

from parsers.base_parser import LanguageParser, ParserFactory
from tools.git_diff_extractor import get_file_content, parse_diff_lines


class JavaParser(LanguageParser):
    """Java-specific security parser using regex patterns."""

    def _define_security_patterns(self) -> Dict[str, List[str]]:
        """Define Java-specific security patterns."""
        return {
            'sql_keywords': ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER'],
            'dangerous_methods': ['Runtime.exec', 'ProcessBuilder', 'Class.forName', 'URLClassLoader'],
            'user_input_sources': ['request.getParameter', 'request.getHeader', 'request.getQueryString',
                                   'HttpServletRequest', 'Scanner', 'BufferedReader'],
            'file_operations': ['FileInputStream', 'FileOutputStream', 'FileReader', 'FileWriter', 'File('],
            'deserialization': ['ObjectInputStream', 'readObject', 'XMLDecoder'],
            'crypto_weak': ['MD5', 'SHA1', 'DES', 'RC4'],
        }

    def parse_file(self, filepath: str, diff_content: str) -> Dict[str, Any]:
        """Parse Java file and extract security-relevant patterns."""
        content = get_file_content(filepath)
        if not content:
            return self._empty_extraction(filepath)

        changed_lines = parse_diff_lines(diff_content)
        tainted_vars = self._find_tainted_variables(content)

        extraction = {
            "filepath": filepath,
            "parseable": True,
            "language": "java",
            "functions": self._extract_functions(content),
            "classes": self._extract_classes(content),
            "sql_patterns": self._find_sql_patterns(content),
            "user_inputs": self._find_user_inputs(content),
            "file_operations": self._find_file_operations(content, tainted_vars),
            "dangerous_methods": self._find_dangerous_methods(content),
            "subprocess_calls": self._find_subprocess_calls(content, tainted_vars),
            "deserialization": self._find_deserialization(content),
            "changed_lines": changed_lines,
            "tainted_variables": list(tainted_vars),
            "has_security_patterns": False
        }

        extraction["has_security_patterns"] = (
            len(extraction["sql_patterns"]) > 0 or
            len(extraction["user_inputs"]) > 0 or
            len(extraction["file_operations"]) > 0 or
            len(extraction["dangerous_methods"]) > 0 or
            len(extraction["subprocess_calls"]) > 0 or
            len(extraction["deserialization"]) > 0
        )

        return extraction

    def _find_tainted_variables(self, content: str) -> Set[str]:
        """Find variables assigned from user input sources."""
        tainted = set()

        for pattern in self.security_patterns['user_input_sources']:
            # Match variable assignments: String x = request.getParameter(...)
            regex = r'(?:\w+)\s+(\w+)\s*=\s*.*?' + re.escape(pattern)
            matches = re.finditer(regex, content)
            for match in matches:
                tainted.add(match.group(1))

        return tainted

    def _extract_functions(self, content: str) -> List[Dict[str, Any]]:
        """Extract method definitions."""
        functions = []

        # Match method declarations: public void methodName(...)
        pattern = r'(?:public|private|protected)?\s+(?:static\s+)?(?:\w+)\s+(\w+)\s*\(([^)]*)\)'
        for match in re.finditer(pattern, content):
            lineno = content[:match.start()].count('\n') + 1
            functions.append({
                "name": match.group(1),
                "lineno": lineno,
                "args": [arg.strip().split()[-1] for arg in match.group(2).split(',') if arg.strip()],
                "type": "method"
            })

        return functions

    def _extract_classes(self, content: str) -> List[Dict[str, Any]]:
        """Extract class definitions."""
        classes = []

        # Match class declarations: public class ClassName
        pattern = r'(?:public|private|protected)?\s+class\s+(\w+)'
        for match in re.finditer(pattern, content):
            lineno = content[:match.start()].count('\n') + 1
            classes.append({
                "name": match.group(1),
                "lineno": lineno
            })

        return classes

    def _find_sql_patterns(self, content: str) -> List[Dict[str, Any]]:
        """Find potential SQL query construction."""
        sql_patterns = []

        for keyword in self.security_patterns['sql_keywords']:
            # Find SQL with string concatenation
            pattern = r'"[^"]*' + keyword + r'[^"]*"\s*\+'
            for match in re.finditer(pattern, content, re.IGNORECASE):
                lineno = content[:match.start()].count('\n') + 1
                sql_patterns.append({
                    "query_snippet": match.group(0)[:100],
                    "lineno": lineno,
                    "uses_formatting": True,
                    "risk": "HIGH"
                })

            # Find SQL with String.format
            pattern = r'String\.format\([^)]*' + keyword + r'[^)]*\)'
            for match in re.finditer(pattern, content, re.IGNORECASE):
                lineno = content[:match.start()].count('\n') + 1
                sql_patterns.append({
                    "query_snippet": match.group(0)[:100],
                    "lineno": lineno,
                    "uses_formatting": True,
                    "risk": "HIGH"
                })

        return sql_patterns

    def _find_user_inputs(self, content: str) -> List[Dict[str, Any]]:
        """Find user input sources."""
        inputs = []

        for pattern in self.security_patterns['user_input_sources']:
            for match in re.finditer(re.escape(pattern), content):
                lineno = content[:match.start()].count('\n') + 1
                inputs.append({
                    "source": pattern,
                    "lineno": lineno,
                    "type": self._classify_input_type(pattern)
                })

        return inputs

    def _find_file_operations(self, content: str, tainted_vars: Set[str]) -> List[Dict[str, Any]]:
        """Find file operations that could be vulnerable."""
        file_ops = []

        for operation in self.security_patterns['file_operations']:
            pattern = r'\b' + re.escape(operation)
            for match in re.finditer(pattern, content):
                lineno = content[:match.start()].count('\n') + 1

                # Check if tainted variable is nearby
                context = content[max(0, match.start()-100):match.end()+100]
                has_user_input = any(var in context for var in tainted_vars)

                file_ops.append({
                    "operation": operation,
                    "lineno": lineno,
                    "has_user_input": has_user_input,
                    "risk": "HIGH" if has_user_input else "LOW"
                })

        return file_ops

    def _find_dangerous_methods(self, content: str) -> List[Dict[str, Any]]:
        """Find dangerous method calls."""
        dangerous = []

        for method in self.security_patterns['dangerous_methods']:
            pattern = r'\b' + re.escape(method)
            for match in re.finditer(pattern, content):
                lineno = content[:match.start()].count('\n') + 1
                dangerous.append({
                    "method": method,
                    "lineno": lineno,
                    "risk": "HIGH"
                })

        return dangerous

    def _find_subprocess_calls(self, content: str, tainted_vars: Set[str]) -> List[Dict[str, Any]]:
        """Find subprocess/command execution calls."""
        subprocess_calls = []

        patterns = ['Runtime.getRuntime().exec', 'ProcessBuilder', 'Runtime.exec']

        for cmd in patterns:
            pattern = re.escape(cmd)
            for match in re.finditer(pattern, content):
                lineno = content[:match.start()].count('\n') + 1

                # Check if tainted variable is nearby
                context = content[max(0, match.start()-100):match.end()+100]
                has_user_input = any(var in context for var in tainted_vars)

                subprocess_calls.append({
                    "function": cmd,
                    "lineno": lineno,
                    "has_user_input": has_user_input,
                    "uses_shell": True,
                    "risk": "CRITICAL" if has_user_input else "HIGH"
                })

        return subprocess_calls

    def _find_deserialization(self, content: str) -> List[Dict[str, Any]]:
        """Find insecure deserialization patterns."""
        deserialization = []

        for pattern in self.security_patterns['deserialization']:
            regex = r'\b' + re.escape(pattern)
            for match in re.finditer(regex, content):
                lineno = content[:match.start()].count('\n') + 1
                deserialization.append({
                    "method": pattern,
                    "lineno": lineno,
                    "risk": "CRITICAL"
                })

        return deserialization

    def _classify_input_type(self, source: str) -> str:
        """Classify the type of user input."""
        if 'getParameter' in source:
            return 'request_param'
        elif 'getHeader' in source:
            return 'http_header'
        elif 'getQueryString' in source:
            return 'query_string'
        elif 'Scanner' in source:
            return 'stdin'
        elif 'BufferedReader' in source:
            return 'stream'
        return 'unknown'


# Register Java parser
ParserFactory.register_parser(['.java'], JavaParser)
