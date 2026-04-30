"""
JavaScript Language Parser
Regex-based pattern matching for JavaScript security analysis.
"""

import re
from typing import Dict, List, Any, Set

from parsers.base_parser import LanguageParser, ParserFactory
from tools.git_diff_extractor import get_file_content, parse_diff_lines


class JavaScriptParser(LanguageParser):
    """JavaScript-specific security parser using regex patterns."""

    def _define_security_patterns(self) -> Dict[str, List[str]]:
        """Define JavaScript-specific security patterns."""
        return {
            'sql_keywords': ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER'],
            'dangerous_functions': ['eval', 'Function', 'setTimeout', 'setInterval', 'execScript'],
            'user_input_sources': ['req.query', 'req.body', 'req.params', 'req.headers',
                                   'window.location', 'document.cookie', 'localStorage', 'sessionStorage'],
            'file_operations': ['fs.readFile', 'fs.writeFile', 'fs.unlink', 'fs.readdir', 'require('],
            'command_execution': ['child_process.exec', 'child_process.spawn', 'child_process.execSync'],
            'crypto_weak': ['md5', 'sha1', 'DES', 'RC4'],
        }

    def parse_file(self, filepath: str, diff_content: str) -> Dict[str, Any]:
        """Parse JavaScript file and extract security-relevant patterns."""
        content = get_file_content(filepath)
        if not content:
            return self._empty_extraction(filepath)

        changed_lines = parse_diff_lines(diff_content)
        tainted_vars = self._find_tainted_variables(content)

        extraction = {
            "filepath": filepath,
            "parseable": True,
            "language": "javascript",
            "functions": self._extract_functions(content),
            "sql_patterns": self._find_sql_patterns(content),
            "user_inputs": self._find_user_inputs(content),
            "file_operations": self._find_file_operations(content, tainted_vars),
            "dangerous_functions": self._find_dangerous_functions(content),
            "subprocess_calls": self._find_subprocess_calls(content, tainted_vars),
            "xss_sinks": self._find_xss_sinks(content, tainted_vars),
            "changed_lines": changed_lines,
            "tainted_variables": list(tainted_vars),
            "has_security_patterns": False
        }

        extraction["has_security_patterns"] = (
            len(extraction["sql_patterns"]) > 0 or
            len(extraction["user_inputs"]) > 0 or
            len(extraction["file_operations"]) > 0 or
            len(extraction["dangerous_functions"]) > 0 or
            len(extraction["subprocess_calls"]) > 0 or
            len(extraction["xss_sinks"]) > 0
        )

        return extraction

    def _find_tainted_variables(self, content: str) -> Set[str]:
        """Find variables assigned from user input sources."""
        tainted = set()

        # Match variable assignments: const/let/var x = req.query...
        for pattern in self.security_patterns['user_input_sources']:
            # Find assignments
            regex = r'(?:const|let|var)\s+(\w+)\s*=\s*.*?' + re.escape(pattern)
            matches = re.finditer(regex, content)
            for match in matches:
                tainted.add(match.group(1))

            # Find destructuring: const { x } = req.query
            regex = r'(?:const|let|var)\s*\{\s*(\w+(?:\s*,\s*\w+)*)\s*\}\s*=\s*.*?' + re.escape(pattern)
            matches = re.finditer(regex, content)
            for match in matches:
                vars_str = match.group(1)
                for var in re.findall(r'\w+', vars_str):
                    tainted.add(var)

        return tainted

    def _extract_functions(self, content: str) -> List[Dict[str, Any]]:
        """Extract function definitions."""
        functions = []

        # Regular function declarations: function name() {}
        pattern = r'function\s+(\w+)\s*\(([^)]*)\)'
        for match in re.finditer(pattern, content):
            lineno = content[:match.start()].count('\n') + 1
            functions.append({
                "name": match.group(1),
                "lineno": lineno,
                "args": [arg.strip() for arg in match.group(2).split(',') if arg.strip()],
                "type": "function"
            })

        # Arrow functions: const name = () => {}
        pattern = r'(?:const|let|var)\s+(\w+)\s*=\s*\([^)]*\)\s*=>'
        for match in re.finditer(pattern, content):
            lineno = content[:match.start()].count('\n') + 1
            functions.append({
                "name": match.group(1),
                "lineno": lineno,
                "args": [],
                "type": "arrow_function"
            })

        # Method definitions: methodName() {}
        pattern = r'(\w+)\s*\([^)]*\)\s*\{'
        for match in re.finditer(pattern, content):
            lineno = content[:match.start()].count('\n') + 1
            functions.append({
                "name": match.group(1),
                "lineno": lineno,
                "args": [],
                "type": "method"
            })

        return functions

    def _find_sql_patterns(self, content: str) -> List[Dict[str, Any]]:
        """Find potential SQL query construction."""
        sql_patterns = []

        for keyword in self.security_patterns['sql_keywords']:
            # Find SQL in strings with template literals
            pattern = r'`[^`]*' + keyword + r'[^`]*\$\{[^}]+\}[^`]*`'
            for match in re.finditer(pattern, content, re.IGNORECASE):
                lineno = content[:match.start()].count('\n') + 1
                sql_patterns.append({
                    "query_snippet": match.group(0)[:100],
                    "lineno": lineno,
                    "uses_formatting": True,
                    "risk": "HIGH"
                })

            # Find SQL with string concatenation
            pattern = r'["\'][^"\']*' + keyword + r'[^"\']*["\'].*?\+'
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
            pattern = re.escape(operation) + r'\s*\([^)]*\)'
            for match in re.finditer(pattern, content):
                lineno = content[:match.start()].count('\n') + 1
                has_user_input = any(var in match.group(0) for var in tainted_vars)

                file_ops.append({
                    "operation": operation,
                    "lineno": lineno,
                    "has_user_input": has_user_input,
                    "risk": "HIGH" if has_user_input else "LOW"
                })

        return file_ops

    def _find_dangerous_functions(self, content: str) -> List[Dict[str, Any]]:
        """Find dangerous function calls like eval()."""
        dangerous = []

        for func in self.security_patterns['dangerous_functions']:
            pattern = r'\b' + re.escape(func) + r'\s*\('
            for match in re.finditer(pattern, content):
                lineno = content[:match.start()].count('\n') + 1
                dangerous.append({
                    "function": func,
                    "lineno": lineno,
                    "risk": "CRITICAL"
                })

        return dangerous

    def _find_subprocess_calls(self, content: str, tainted_vars: Set[str]) -> List[Dict[str, Any]]:
        """Find subprocess/command execution calls."""
        subprocess_calls = []

        for cmd in self.security_patterns['command_execution']:
            pattern = re.escape(cmd) + r'\s*\([^)]*\)'
            for match in re.finditer(pattern, content):
                lineno = content[:match.start()].count('\n') + 1
                has_user_input = any(var in match.group(0) for var in tainted_vars)

                subprocess_calls.append({
                    "function": cmd,
                    "lineno": lineno,
                    "has_user_input": has_user_input,
                    "uses_shell": True,  # Assume shell usage in JS
                    "risk": "CRITICAL" if has_user_input else "HIGH"
                })

        return subprocess_calls

    def _find_xss_sinks(self, content: str, tainted_vars: Set[str]) -> List[Dict[str, Any]]:
        """Find XSS sinks (DOM manipulation with user input)."""
        xss_sinks = []

        dangerous_sinks = [
            'innerHTML', 'outerHTML', 'document.write', 'document.writeln',
            'eval', 'setTimeout', 'setInterval', 'Function'
        ]

        for sink in dangerous_sinks:
            pattern = r'\.' + re.escape(sink) + r'\s*[=\(]'
            for match in re.finditer(pattern, content):
                lineno = content[:match.start()].count('\n') + 1

                # Check if tainted variable is nearby
                context = content[max(0, match.start()-100):match.end()+100]
                has_user_input = any(var in context for var in tainted_vars)

                xss_sinks.append({
                    "sink": sink,
                    "lineno": lineno,
                    "has_user_input": has_user_input,
                    "risk": "HIGH" if has_user_input else "MEDIUM"
                })

        return xss_sinks

    def _classify_input_type(self, source: str) -> str:
        """Classify the type of user input."""
        if 'req.query' in source:
            return 'query_param'
        elif 'req.body' in source:
            return 'request_body'
        elif 'req.params' in source:
            return 'url_param'
        elif 'req.headers' in source:
            return 'http_header'
        elif 'window.location' in source:
            return 'url'
        elif 'document.cookie' in source:
            return 'cookie'
        elif 'localStorage' in source or 'sessionStorage' in source:
            return 'storage'
        return 'unknown'


# Register JavaScript parser
ParserFactory.register_parser(['.js', '.jsx', '.mjs', '.cjs'], JavaScriptParser)
