"""
Go Language Parser
Regex-based pattern matching for Go security analysis.
"""

import re
from typing import Dict, List, Any, Set

from parsers.base_parser import LanguageParser, ParserFactory
from tools.git_diff_extractor import get_file_content, parse_diff_lines


class GoParser(LanguageParser):
    """Go-specific security parser using regex patterns."""

    def _define_security_patterns(self) -> Dict[str, List[str]]:
        """Define Go-specific security patterns."""
        return {
            'sql_keywords': ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER'],
            'dangerous_functions': ['exec.Command', 'os.Exec', 'syscall.Exec', 'eval'],
            'user_input_sources': ['r.FormValue', 'r.PostFormValue', 'r.URL.Query', 'r.Header',
                                   'os.Args', 'flag.String', 'bufio.Scanner'],
            'file_operations': ['os.Open', 'os.Create', 'os.ReadFile', 'os.WriteFile', 'ioutil.ReadFile'],
            'command_execution': ['exec.Command', 'exec.CommandContext', 'os.StartProcess'],
            'crypto_weak': ['md5', 'sha1', 'des', 'rc4'],
        }

    def parse_file(self, filepath: str, diff_content: str) -> Dict[str, Any]:
        """Parse Go file and extract security-relevant patterns."""
        content = get_file_content(filepath)
        if not content:
            return self._empty_extraction(filepath)

        changed_lines = parse_diff_lines(diff_content)
        tainted_vars = self._find_tainted_variables(content)

        extraction = {
            "filepath": filepath,
            "parseable": True,
            "language": "go",
            "functions": self._extract_functions(content),
            "sql_patterns": self._find_sql_patterns(content),
            "user_inputs": self._find_user_inputs(content),
            "file_operations": self._find_file_operations(content, tainted_vars),
            "dangerous_functions": self._find_dangerous_functions(content),
            "subprocess_calls": self._find_subprocess_calls(content, tainted_vars),
            "changed_lines": changed_lines,
            "tainted_variables": list(tainted_vars),
            "has_security_patterns": False
        }

        extraction["has_security_patterns"] = (
            len(extraction["sql_patterns"]) > 0 or
            len(extraction["user_inputs"]) > 0 or
            len(extraction["file_operations"]) > 0 or
            len(extraction["dangerous_functions"]) > 0 or
            len(extraction["subprocess_calls"]) > 0
        )

        return extraction

    def _find_tainted_variables(self, content: str) -> Set[str]:
        """Find variables assigned from user input sources."""
        tainted = set()

        for pattern in self.security_patterns['user_input_sources']:
            # Match variable assignments: x := r.FormValue(...)
            regex = r'(\w+)\s*:=\s*.*?' + re.escape(pattern)
            matches = re.finditer(regex, content)
            for match in matches:
                tainted.add(match.group(1))

            # Match var declarations: var x = r.FormValue(...)
            regex = r'var\s+(\w+)(?:\s+\w+)?\s*=\s*.*?' + re.escape(pattern)
            matches = re.finditer(regex, content)
            for match in matches:
                tainted.add(match.group(1))

        return tainted

    def _extract_functions(self, content: str) -> List[Dict[str, Any]]:
        """Extract function definitions."""
        functions = []

        # Match function declarations: func name(...) {...}
        pattern = r'func\s+(?:\([^)]*\)\s+)?(\w+)\s*\(([^)]*)\)'
        for match in re.finditer(pattern, content):
            lineno = content[:match.start()].count('\n') + 1

            # Parse parameters
            params_str = match.group(2)
            args = []
            if params_str.strip():
                # Simple parsing - just extract parameter names
                for param in params_str.split(','):
                    parts = param.strip().split()
                    if parts:
                        args.append(parts[0])

            functions.append({
                "name": match.group(1),
                "lineno": lineno,
                "args": args,
                "type": "function"
            })

        return functions

    def _find_sql_patterns(self, content: str) -> List[Dict[str, Any]]:
        """Find potential SQL query construction."""
        sql_patterns = []

        for keyword in self.security_patterns['sql_keywords']:
            # Find SQL with fmt.Sprintf
            pattern = r'fmt\.Sprintf\([^)]*' + keyword + r'[^)]*\)'
            for match in re.finditer(pattern, content, re.IGNORECASE):
                lineno = content[:match.start()].count('\n') + 1
                sql_patterns.append({
                    "query_snippet": match.group(0)[:100],
                    "lineno": lineno,
                    "uses_formatting": True,
                    "risk": "HIGH"
                })

            # Find SQL with string concatenation using +
            pattern = r'`[^`]*' + keyword + r'[^`]*`\s*\+'
            for match in re.finditer(pattern, content, re.IGNORECASE):
                lineno = content[:match.start()].count('\n') + 1
                sql_patterns.append({
                    "query_snippet": match.group(0)[:100],
                    "lineno": lineno,
                    "uses_formatting": True,
                    "risk": "HIGH"
                })

            # Find SQL in regular strings with concatenation
            pattern = r'"[^"]*' + keyword + r'[^"]*"\s*\+'
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
        """Find dangerous function calls."""
        dangerous = []

        for func in self.security_patterns['dangerous_functions']:
            pattern = r'\b' + re.escape(func) + r'\s*\('
            for match in re.finditer(pattern, content):
                lineno = content[:match.start()].count('\n') + 1
                dangerous.append({
                    "function": func,
                    "lineno": lineno,
                    "risk": "HIGH"
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
                    "uses_shell": False,  # Go exec doesn't use shell by default
                    "risk": "CRITICAL" if has_user_input else "HIGH"
                })

        return subprocess_calls

    def _classify_input_type(self, source: str) -> str:
        """Classify the type of user input."""
        if 'FormValue' in source or 'PostFormValue' in source:
            return 'form_data'
        elif 'URL.Query' in source:
            return 'query_param'
        elif 'Header' in source:
            return 'http_header'
        elif 'os.Args' in source:
            return 'cli_arg'
        elif 'flag.String' in source:
            return 'flag'
        elif 'Scanner' in source:
            return 'stdin'
        return 'unknown'


# Register Go parser
ParserFactory.register_parser(['.go'], GoParser)
