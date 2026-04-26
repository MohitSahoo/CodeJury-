"""
Stage 1: Code Parsing & AST Analysis
Extracts security-relevant patterns from Python code using AST.
"""

import ast
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

from tools.git_diff_extractor import (
    get_staged_python_files,
    get_file_content,
    get_file_diff,
    parse_diff_lines
)


class SecurityCodeParser:
    """Parse Python code and extract security-relevant patterns."""

    def __init__(self):
        self.security_patterns = {
            'sql_keywords': ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER'],
            'dangerous_imports': ['subprocess', 'os.system', 'eval', 'exec', 'pickle', '__import__'],
            'user_input_sources': ['request.args', 'request.form', 'request.json', 'request.data',
                                   'request.files', 'request.values', 'input(', 'sys.argv'],
            'file_operations': ['open(', 'file(', 'Path(', 'os.path.join'],
            'crypto_weak': ['md5', 'sha1', 'DES', 'RC4'],
        }

    def parse_file(self, filepath: str, diff_content: str) -> Dict[str, Any]:
        """
        Parse Python file and extract security-relevant patterns.

        Args:
            filepath: Path to Python file
            diff_content: Git diff for this file

        Returns:
            Dictionary with extracted security patterns
        """
        content = get_file_content(filepath)
        if not content:
            return self._empty_extraction(filepath)

        try:
            tree = ast.parse(content, filename=filepath)
        except SyntaxError as e:
            return {
                "filepath": filepath,
                "error": f"Syntax error: {e}",
                "parseable": False
            }

        changed_lines = parse_diff_lines(diff_content)

        # Build tainted variable set for data flow tracking
        tainted_vars = self._find_tainted_variables(tree)

        extraction = {
            "filepath": filepath,
            "parseable": True,
            "functions": self._extract_functions(tree, changed_lines),
            "classes": self._extract_classes(tree),
            "sql_patterns": self._find_sql_patterns(tree, content),
            "user_inputs": self._find_user_inputs(tree, content),
            "file_operations": self._find_file_operations(tree, content, tainted_vars),
            "dangerous_imports": self._extract_dangerous_imports(tree),
            "string_formatting": self._find_string_formatting(tree, content),
            "subprocess_calls": self._find_subprocess_calls(tree, content, tainted_vars),
            "changed_lines": changed_lines,
            "tainted_variables": list(tainted_vars),
            "has_security_patterns": False  # Will be set below
        }

        # Determine if file has security-relevant patterns
        extraction["has_security_patterns"] = (
            len(extraction["sql_patterns"]) > 0 or
            len(extraction["user_inputs"]) > 0 or
            len(extraction["file_operations"]) > 0 or
            len(extraction["dangerous_imports"]) > 0 or
            len(extraction["subprocess_calls"]) > 0
        )

        return extraction

    def _empty_extraction(self, filepath: str) -> Dict[str, Any]:
        """Return empty extraction structure."""
        return {
            "filepath": filepath,
            "parseable": False,
            "error": "Could not read file",
            "has_security_patterns": False
        }

    def _find_tainted_variables(self, tree: ast.AST) -> set:
        """
        Find variables assigned from user input sources (taint tracking).
        Returns set of variable names that contain user input.
        """
        tainted = set()

        for node in ast.walk(tree):
            # Check assignments: var = request.args.get('x')
            if isinstance(node, ast.Assign):
                # Check if RHS contains user input
                rhs_str = ast.unparse(node.value)
                if any(pattern in rhs_str for pattern in self.security_patterns['user_input_sources']):
                    # Mark all LHS targets as tainted
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            tainted.add(target.id)

            # Check augmented assignments: var += request.args.get('x')
            elif isinstance(node, ast.AugAssign):
                rhs_str = ast.unparse(node.value)
                if any(pattern in rhs_str for pattern in self.security_patterns['user_input_sources']):
                    if isinstance(node.target, ast.Name):
                        tainted.add(node.target.id)

        return tainted

    def _extract_functions(self, tree: ast.AST, changed_lines: Dict[str, List[int]]) -> List[Dict[str, Any]]:
        """Extract all function definitions."""
        functions = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_info = {
                    "name": node.name,
                    "lineno": node.lineno,
                    "end_lineno": getattr(node, 'end_lineno', node.lineno),
                    "args": [arg.arg for arg in node.args.args],
                    "decorators": [ast.unparse(d) for d in node.decorator_list],
                    "is_async": isinstance(node, ast.AsyncFunctionDef),
                    "in_changed_lines": self._overlaps_changed_lines(
                        node.lineno,
                        getattr(node, 'end_lineno', node.lineno),
                        changed_lines.get('added', [])
                    )
                }
                functions.append(func_info)

        return functions

    def _extract_classes(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract class definitions."""
        classes = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_info = {
                    "name": node.name,
                    "lineno": node.lineno,
                    "bases": [ast.unparse(base) for base in node.bases],
                    "methods": [m.name for m in node.body if isinstance(m, ast.FunctionDef)]
                }
                classes.append(class_info)

        return classes

    def _find_sql_patterns(self, tree: ast.AST, content: str) -> List[Dict[str, Any]]:
        """Find potential SQL query construction."""
        sql_patterns = []

        for node in ast.walk(tree):
            # Check string literals for SQL keywords
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                sql_upper = node.value.upper()
                if any(kw in sql_upper for kw in self.security_patterns['sql_keywords']):
                    # Check if it's using f-string or format (dangerous)
                    parent = self._get_parent_node(tree, node)
                    is_formatted = isinstance(parent, (ast.JoinedStr, ast.FormattedValue))

                    sql_patterns.append({
                        "query_snippet": node.value[:100],  # First 100 chars
                        "lineno": node.lineno,
                        "uses_formatting": is_formatted,
                        "risk": "HIGH" if is_formatted else "MEDIUM"
                    })

            # Check for .format() calls on strings with SQL
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute) and node.func.attr == 'format':
                    if isinstance(node.func.value, ast.Constant):
                        sql_upper = str(node.func.value.value).upper()
                        if any(kw in sql_upper for kw in self.security_patterns['sql_keywords']):
                            sql_patterns.append({
                                "query_snippet": str(node.func.value.value)[:100],
                                "lineno": node.lineno,
                                "uses_formatting": True,
                                "risk": "HIGH"
                            })

        return sql_patterns

    def _find_user_inputs(self, tree: ast.AST, content: str) -> List[Dict[str, Any]]:
        """Find user input sources (request.args, request.form, etc)."""
        inputs = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                source = ast.unparse(node)
                if any(pattern in source for pattern in self.security_patterns['user_input_sources']):
                    inputs.append({
                        "source": source,
                        "lineno": node.lineno,
                        "type": self._classify_input_type(source)
                    })

            # Check for input() calls
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == 'input':
                    inputs.append({
                        "source": "input()",
                        "lineno": node.lineno,
                        "type": "stdin"
                    })

        return inputs

    def _find_file_operations(self, tree: ast.AST, content: str, tainted_vars: set) -> List[Dict[str, Any]]:
        """Find file operations that could be vulnerable to path traversal."""
        file_ops = []

        for node in ast.walk(tree):
            # Check direct function calls
            if isinstance(node, ast.Call):
                func_name = ""
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = ast.unparse(node.func)

                # Check if it's a file operation
                if func_name == 'open' or 'Path' in func_name or 'os.path' in func_name:
                    has_user_input = self._contains_user_input(node, tainted_vars)

                    file_ops.append({
                        "operation": func_name,
                        "lineno": node.lineno,
                        "has_user_input": has_user_input,
                        "risk": "HIGH" if has_user_input else "LOW"
                    })

            # Check with statements (with open(...) as f:)
            elif isinstance(node, ast.With):
                for item in node.items:
                    if isinstance(item.context_expr, ast.Call):
                        func_name = ""
                        if isinstance(item.context_expr.func, ast.Name):
                            func_name = item.context_expr.func.id

                        if func_name == 'open':
                            has_user_input = self._contains_user_input(item.context_expr, tainted_vars)

                            file_ops.append({
                                "operation": f"with {func_name}()",
                                "lineno": node.lineno,
                                "has_user_input": has_user_input,
                                "risk": "HIGH" if has_user_input else "LOW"
                            })

        return file_ops

    def _extract_dangerous_imports(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract potentially dangerous imports."""
        dangerous = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if any(danger in alias.name for danger in self.security_patterns['dangerous_imports']):
                        dangerous.append({
                            "module": alias.name,
                            "lineno": node.lineno,
                            "type": "import"
                        })

            elif isinstance(node, ast.ImportFrom):
                if node.module and any(danger in node.module for danger in self.security_patterns['dangerous_imports']):
                    dangerous.append({
                        "module": node.module,
                        "lineno": node.lineno,
                        "type": "from_import"
                    })

        return dangerous

    def _find_string_formatting(self, tree: ast.AST, content: str) -> List[Dict[str, Any]]:
        """Find string formatting that might be used in SQL/command injection."""
        formatting = []

        for node in ast.walk(tree):
            # F-strings
            if isinstance(node, ast.JoinedStr):
                formatting.append({
                    "type": "f-string",
                    "lineno": node.lineno,
                    "risk": "MEDIUM"
                })

            # .format() calls
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute) and node.func.attr == 'format':
                    formatting.append({
                        "type": ".format()",
                        "lineno": node.lineno,
                        "risk": "MEDIUM"
                    })

            # % formatting
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod):
                if isinstance(node.left, ast.Constant) and isinstance(node.left.value, str):
                    formatting.append({
                        "type": "% formatting",
                        "lineno": node.lineno,
                        "risk": "MEDIUM"
                    })

        return formatting

    def _find_subprocess_calls(self, tree: ast.AST, content: str, tainted_vars: set) -> List[Dict[str, Any]]:
        """Find subprocess/os.system calls that could lead to command injection."""
        subprocess_calls = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = ast.unparse(node.func) if hasattr(node, 'func') else ""

                if 'subprocess' in func_name or 'os.system' in func_name or 'os.popen' in func_name:
                    has_user_input = self._contains_user_input(node, tainted_vars)
                    uses_shell = self._uses_shell_true(node)

                    subprocess_calls.append({
                        "function": func_name,
                        "lineno": node.lineno,
                        "has_user_input": has_user_input,
                        "uses_shell": uses_shell,
                        "risk": "CRITICAL" if (has_user_input and uses_shell) else "HIGH" if has_user_input else "MEDIUM"
                    })

        return subprocess_calls

    def _contains_user_input(self, node: ast.AST, tainted_vars: set) -> bool:
        """
        Check if node contains references to user input sources or tainted variables.

        Args:
            node: AST node to check
            tainted_vars: Set of variable names known to contain user input

        Returns:
            True if node contains user input (direct or via tainted variable)
        """
        node_str = ast.unparse(node)

        # Check direct user input patterns
        if any(pattern in node_str for pattern in self.security_patterns['user_input_sources']):
            return True

        # Check if any tainted variables are referenced in this node
        for var_name in tainted_vars:
            # Check for variable usage (not just substring match)
            # Look for the variable as a Name node
            for child in ast.walk(node):
                if isinstance(child, ast.Name) and child.id == var_name:
                    return True

        return False

    def _uses_shell_true(self, node: ast.Call) -> bool:
        """Check if subprocess call uses shell=True."""
        for keyword in node.keywords:
            if keyword.arg == 'shell':
                if isinstance(keyword.value, ast.Constant) and keyword.value.value is True:
                    return True
        return False

    def _classify_input_type(self, source: str) -> str:
        """Classify the type of user input."""
        if 'request.args' in source:
            return 'query_param'
        elif 'request.form' in source:
            return 'form_data'
        elif 'request.json' in source:
            return 'json_body'
        elif 'request.files' in source:
            return 'file_upload'
        elif 'input(' in source:
            return 'stdin'
        elif 'sys.argv' in source:
            return 'cli_arg'
        return 'unknown'

    def _overlaps_changed_lines(self, start: int, end: int, changed_lines: List[int]) -> bool:
        """Check if function overlaps with changed lines."""
        return any(start <= line <= end for line in changed_lines)

    def _get_parent_node(self, tree: ast.AST, target: ast.AST) -> Optional[ast.AST]:
        """Get parent node of target (simplified - walks tree)."""
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                if child == target:
                    return node
        return None


def run_stage1() -> List[Dict[str, Any]]:
    """
    Stage 1: Parse all staged Python files.

    Returns:
        List of extraction dictionaries
    """
    # Check cache first
    cache_file = Path('cache/stage1_extraction.json')
    if cache_file.exists():
        print("✓ Stage 1 cache found, loading...")
        with open(cache_file) as f:
            return json.load(f)

    print("Stage 1: Code Parsing & AST Analysis")
    print("=" * 50)

    staged_files = get_staged_python_files()

    if not staged_files:
        print("No Python files staged")
        return []

    print(f"Found {len(staged_files)} staged Python file(s)")

    parser = SecurityCodeParser()
    extractions = []

    for filepath in staged_files:
        print(f"\nParsing: {filepath}")
        diff = get_file_diff(filepath)
        extraction = parser.parse_file(filepath, diff)

        if extraction.get('parseable'):
            print(f"  ✓ Functions: {len(extraction['functions'])}")
            print(f"  ✓ SQL patterns: {len(extraction['sql_patterns'])}")
            print(f"  ✓ User inputs: {len(extraction['user_inputs'])}")
            print(f"  ✓ File operations: {len(extraction['file_operations'])}")
            print(f"  ✓ Dangerous imports: {len(extraction['dangerous_imports'])}")
            print(f"  ✓ Subprocess calls: {len(extraction['subprocess_calls'])}")

            if extraction['has_security_patterns']:
                print(f"  ⚠ Has security-relevant patterns - will analyze")
            else:
                print(f"  ✓ No security patterns - will skip analysis")
        else:
            print(f"  ✗ Parse error: {extraction.get('error')}")

        extractions.append(extraction)

    # Cache results
    cache_file.parent.mkdir(exist_ok=True)
    with open(cache_file, 'w') as f:
        json.dump(extractions, f, indent=2)

    print(f"\n✓ Stage 1 complete - cached to {cache_file}")

    return extractions


if __name__ == "__main__":
    # Test Stage 1
    extractions = run_stage1()
    print(f"\nExtracted {len(extractions)} file(s)")

    security_relevant = sum(1 for e in extractions if e.get('has_security_patterns'))
    print(f"Security-relevant files: {security_relevant}")
