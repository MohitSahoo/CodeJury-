"""
Python Language Parser
Refactored from original SecurityCodeParser.
"""

import ast
from typing import Dict, List, Any, Set, Optional

from parsers.base_parser import LanguageParser, ParserFactory
from tools.git_diff_extractor import get_file_content, parse_diff_lines


class PythonParser(LanguageParser):
    """Python-specific security parser using AST."""

    def _define_security_patterns(self) -> Dict[str, List[str]]:
        """Define Python-specific security patterns."""
        return {
            'sql_keywords': ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER'],
            'dangerous_imports': ['subprocess', 'os.system', 'eval', 'exec', 'pickle', '__import__'],
            'user_input_sources': ['request.args', 'request.form', 'request.json', 'request.data',
                                   'request.files', 'request.values', 'input(', 'sys.argv'],
            'file_operations': ['open(', 'file(', 'Path(', 'os.path.join'],
            'crypto_weak': ['md5', 'sha1', 'DES', 'RC4'],
        }

    def parse_file(self, filepath: str, diff_content: str) -> Dict[str, Any]:
        """Parse Python file and extract security-relevant patterns."""
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
        tainted_vars = self._find_tainted_variables_ast(tree)

        extraction = {
            "filepath": filepath,
            "parseable": True,
            "language": "python",
            "functions": self._extract_functions_ast(tree, changed_lines),
            "classes": self._extract_classes(tree),
            "sql_patterns": self._find_sql_patterns_ast(tree, content),
            "user_inputs": self._find_user_inputs_ast(tree),
            "file_operations": self._find_file_operations_ast(tree, tainted_vars),
            "dangerous_imports": self._extract_dangerous_imports(tree),
            "string_formatting": self._find_string_formatting(tree),
            "subprocess_calls": self._find_subprocess_calls_ast(tree, tainted_vars),
            "changed_lines": changed_lines,
            "tainted_variables": list(tainted_vars),
            "has_security_patterns": False
        }

        extraction["has_security_patterns"] = (
            len(extraction["sql_patterns"]) > 0 or
            len(extraction["user_inputs"]) > 0 or
            len(extraction["file_operations"]) > 0 or
            len(extraction["dangerous_imports"]) > 0 or
            len(extraction["subprocess_calls"]) > 0
        )

        return extraction

    def _find_tainted_variables(self, content: str) -> Set[str]:
        """Find tainted variables from source code string."""
        try:
            tree = ast.parse(content)
            return self._find_tainted_variables_ast(tree)
        except SyntaxError:
            return set()

    def _find_tainted_variables_ast(self, tree: ast.AST) -> Set[str]:
        """Find variables assigned from user input sources."""
        tainted = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                rhs_str = ast.unparse(node.value)
                if any(pattern in rhs_str for pattern in self.security_patterns['user_input_sources']):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            tainted.add(target.id)

            elif isinstance(node, ast.AugAssign):
                rhs_str = ast.unparse(node.value)
                if any(pattern in rhs_str for pattern in self.security_patterns['user_input_sources']):
                    if isinstance(node.target, ast.Name):
                        tainted.add(node.target.id)

        return tainted

    def _extract_functions(self, content: str) -> List[Dict[str, Any]]:
        """Extract functions from source code string."""
        try:
            tree = ast.parse(content)
            return self._extract_functions_ast(tree, {})
        except SyntaxError:
            return []

    def _extract_functions_ast(self, tree: ast.AST, changed_lines: Dict[str, List[int]]) -> List[Dict[str, Any]]:
        """Extract all function definitions."""
        functions = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
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

    def _find_sql_patterns(self, content: str) -> List[Dict[str, Any]]:
        """Find SQL patterns from source code string."""
        try:
            tree = ast.parse(content)
            return self._find_sql_patterns_ast(tree, content)
        except SyntaxError:
            return []

    def _find_sql_patterns_ast(self, tree: ast.AST, content: str) -> List[Dict[str, Any]]:
        """Find potential SQL query construction."""
        sql_patterns = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                # Skip if it's a docstring
                parent = self._get_parent_node(tree, node)
                if isinstance(parent, ast.Expr) and parent == self._get_docstring_node(tree, node):
                    continue

                sql_upper = node.value.upper()
                if any(kw in sql_upper for kw in self.security_patterns['sql_keywords']):
                    # Additional check: ensure it's not JUST a word like "update" in a sentence
                    is_real_sql = False
                    # Stricter matching for SQL queries
                    if "SELECT" in sql_upper and "FROM" in sql_upper:
                        is_real_sql = True
                    elif any(sql_upper.strip().startswith(kw) for kw in self.security_patterns['sql_keywords']):
                        is_real_sql = True
                    elif "INSERT INTO" in sql_upper or "UPDATE " in sql_upper or "DELETE FROM" in sql_upper:
                        # Ensure it's not part of a word like "UPDATE" in "CREATE/UPDATE"
                        # We look for "UPDATE " but need to be careful
                        if "UPDATE " in sql_upper:
                            # Simple check: is it preceded by something that's not a slash or letter?
                            idx = sql_upper.find("UPDATE ")
                            if idx == 0 or not sql_upper[idx-1].isalnum():
                                is_real_sql = True
                        else:
                            is_real_sql = True
                        
                    if not is_real_sql:
                        continue

                    parent = self._get_parent_node(tree, node)
                    is_formatted = isinstance(parent, (ast.JoinedStr, ast.FormattedValue))

                    sql_patterns.append({
                        "query_snippet": node.value[:100],
                        "lineno": node.lineno,
                        "uses_formatting": is_formatted,
                        "risk": "HIGH" if is_formatted else "MEDIUM"
                    })

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

    def _find_user_inputs(self, content: str) -> List[Dict[str, Any]]:
        """Find user inputs from source code string."""
        try:
            tree = ast.parse(content)
            return self._find_user_inputs_ast(tree)
        except SyntaxError:
            return []

    def _find_user_inputs_ast(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Find user input sources."""
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

            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == 'input':
                    inputs.append({
                        "source": "input()",
                        "lineno": node.lineno,
                        "type": "stdin"
                    })

        return inputs

    def _find_file_operations(self, content: str, tainted_vars: Set[str]) -> List[Dict[str, Any]]:
        """Find file operations from source code string."""
        try:
            tree = ast.parse(content)
            return self._find_file_operations_ast(tree, tainted_vars)
        except SyntaxError:
            return []

    def _find_file_operations_ast(self, tree: ast.AST, tainted_vars: Set[str]) -> List[Dict[str, Any]]:
        """Find file operations that could be vulnerable."""
        file_ops = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = ""
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = ast.unparse(node.func)

                if func_name == 'open' or 'Path' in func_name or 'os.path' in func_name:
                    has_user_input = self._contains_user_input(node, tainted_vars)

                    file_ops.append({
                        "operation": func_name,
                        "lineno": node.lineno,
                        "has_user_input": has_user_input,
                        "risk": "HIGH" if has_user_input else "LOW"
                    })

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

    def _find_subprocess_calls(self, content: str, tainted_vars: Set[str]) -> List[Dict[str, Any]]:
        """Find subprocess calls from source code string."""
        try:
            tree = ast.parse(content)
            return self._find_subprocess_calls_ast(tree, tainted_vars)
        except SyntaxError:
            return []

    def _find_subprocess_calls_ast(self, tree: ast.AST, tainted_vars: Set[str]) -> List[Dict[str, Any]]:
        """Find subprocess/os.system calls."""
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

    def _find_string_formatting(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Find string formatting that might be used in SQL/command injection."""
        formatting = []

        for node in ast.walk(tree):
            if isinstance(node, ast.JoinedStr):
                formatting.append({
                    "type": "f-string",
                    "lineno": node.lineno,
                    "risk": "MEDIUM"
                })

            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute) and node.func.attr == 'format':
                    formatting.append({
                        "type": ".format()",
                        "lineno": node.lineno,
                        "risk": "MEDIUM"
                    })

            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod):
                if isinstance(node.left, ast.Constant) and isinstance(node.left.value, str):
                    formatting.append({
                        "type": "% formatting",
                        "lineno": node.lineno,
                        "risk": "MEDIUM"
                    })

        return formatting

    def _contains_user_input(self, node: ast.AST, tainted_vars: Set[str]) -> bool:
        """Check if node contains references to user input sources or tainted variables."""
        node_str = ast.unparse(node)

        if any(pattern in node_str for pattern in self.security_patterns['user_input_sources']):
            return True

        for var_name in tainted_vars:
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

    def _get_parent_node(self, tree: ast.AST, target: ast.AST):
        """Get parent node of target."""
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                if child == target:
                    return node
        return None

    def _get_docstring_node(self, tree: ast.AST, target_constant: ast.Constant) -> Optional[ast.AST]:
        """Check if target_constant is a docstring of any module/class/function."""
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                if (node.body and 
                    isinstance(node.body[0], ast.Expr) and 
                    isinstance(node.body[0].value, ast.Constant) and 
                    isinstance(node.body[0].value.value, str)):
                    if node.body[0].value == target_constant:
                        return node.body[0]
        return None


# Register Python parser
ParserFactory.register_parser(['.py'], PythonParser)
