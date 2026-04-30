"""
Call Graph Analyzer
Builds project-wide call graph for cross-file data flow analysis.
"""

import ast
from pathlib import Path
from typing import Dict, List, Set, Any, Optional
from collections import defaultdict


class CallGraphNode:
    """Represents a function/method in the call graph."""

    def __init__(self, name: str, filepath: str, lineno: int):
        self.name = name
        self.filepath = filepath
        self.lineno = lineno
        self.calls: Set[str] = set()  # Functions this node calls
        self.called_by: Set[str] = set()  # Functions that call this node
        self.parameters: List[str] = []
        self.returns_tainted: bool = False
        self.accepts_tainted: bool = False

    def __repr__(self):
        return f"<CallGraphNode {self.name} at {self.filepath}:{self.lineno}>"


class CallGraph:
    """Project-wide call graph."""

    def __init__(self):
        self.nodes: Dict[str, CallGraphNode] = {}  # Qualified name -> node
        self.imports: Dict[str, Dict[str, str]] = {}  # filepath -> {alias: module}
        self.file_functions: Dict[str, List[str]] = defaultdict(list)  # filepath -> function names

    def add_node(self, qualified_name: str, node: CallGraphNode):
        """Add a function node to the graph."""
        self.nodes[qualified_name] = node
        self.file_functions[node.filepath].append(qualified_name)

    def add_call(self, caller: str, callee: str):
        """Add a call edge from caller to callee."""
        if caller in self.nodes:
            self.nodes[caller].calls.add(callee)
        if callee in self.nodes:
            self.nodes[callee].called_by.add(caller)

    def get_call_chain(self, start: str, max_depth: int = 5) -> List[List[str]]:
        """
        Get all call chains starting from a function.

        Args:
            start: Starting function qualified name
            max_depth: Maximum chain depth

        Returns:
            List of call chains (each chain is a list of function names)
        """
        chains = []
        visited = set()

        def dfs(current: str, chain: List[str], depth: int):
            if depth > max_depth or current in visited:
                return

            visited.add(current)
            chain.append(current)

            if current in self.nodes:
                calls = self.nodes[current].calls
                if not calls:
                    chains.append(chain.copy())
                else:
                    for callee in calls:
                        dfs(callee, chain.copy(), depth + 1)

            visited.remove(current)

        dfs(start, [], 0)
        return chains

    def get_callers(self, function: str) -> Set[str]:
        """Get all functions that call the given function."""
        if function in self.nodes:
            return self.nodes[function].called_by
        return set()

    def get_callees(self, function: str) -> Set[str]:
        """Get all functions called by the given function."""
        if function in self.nodes:
            return self.nodes[function].calls
        return set()

    def find_paths(self, start: str, end: str, max_depth: int = 5) -> List[List[str]]:
        """
        Find all paths from start function to end function.

        Args:
            start: Starting function
            end: Target function
            max_depth: Maximum path length

        Returns:
            List of paths (each path is a list of function names)
        """
        paths = []
        visited = set()

        def dfs(current: str, path: List[str], depth: int):
            if depth > max_depth or current in visited:
                return

            path.append(current)

            if current == end:
                paths.append(path.copy())
                path.pop()
                return

            visited.add(current)

            if current in self.nodes:
                for callee in self.nodes[current].calls:
                    dfs(callee, path.copy(), depth + 1)

            visited.remove(current)

        dfs(start, [], 0)
        return paths


class CallGraphBuilder:
    """Builds call graph from Python source files."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.graph = CallGraph()

    def build_from_files(self, filepaths: List[str]) -> CallGraph:
        """
        Build call graph from list of Python files.

        Args:
            filepaths: List of Python file paths

        Returns:
            CallGraph object
        """
        # First pass: collect all function definitions and imports
        for filepath in filepaths:
            self._parse_file_definitions(filepath)

        # Second pass: resolve function calls
        for filepath in filepaths:
            self._parse_file_calls(filepath)

        return self.graph

    def _parse_file_definitions(self, filepath: str):
        """Parse file to extract function definitions and imports."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            tree = ast.parse(content, filename=filepath)
        except (SyntaxError, FileNotFoundError, UnicodeDecodeError):
            return

        # Extract imports
        imports = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    imports[name] = alias.name
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    for alias in node.names:
                        name = alias.asname if alias.asname else alias.name
                        imports[name] = f"{node.module}.{alias.name}"

        self.graph.imports[filepath] = imports

        # Extract function definitions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                qualified_name = self._get_qualified_name(filepath, node.name)

                func_node = CallGraphNode(
                    name=node.name,
                    filepath=filepath,
                    lineno=node.lineno
                )
                func_node.parameters = [arg.arg for arg in node.args.args]

                self.graph.add_node(qualified_name, func_node)

    def _parse_file_calls(self, filepath: str):
        """Parse file to extract function calls."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            tree = ast.parse(content, filename=filepath)
        except (SyntaxError, FileNotFoundError, UnicodeDecodeError):
            return

        # Track current function context
        current_function = None

        for node in ast.walk(tree):
            # Track function context
            if isinstance(node, ast.FunctionDef):
                current_function = self._get_qualified_name(filepath, node.name)

            # Extract function calls
            if isinstance(node, ast.Call) and current_function:
                callee_name = self._resolve_call_target(node, filepath)
                if callee_name:
                    self.graph.add_call(current_function, callee_name)

    def _resolve_call_target(self, call_node: ast.Call, filepath: str) -> Optional[str]:
        """
        Resolve the target of a function call.

        Args:
            call_node: AST Call node
            filepath: File containing the call

        Returns:
            Qualified name of the called function, or None if unresolvable
        """
        func = call_node.func

        # Simple function call: func()
        if isinstance(func, ast.Name):
            func_name = func.id

            # Check if it's an imported function
            imports = self.graph.imports.get(filepath, {})
            if func_name in imports:
                module_path = imports[func_name]
                return f"{module_path}"

            # Check if it's a local function
            local_qualified = self._get_qualified_name(filepath, func_name)
            if local_qualified in self.graph.nodes:
                return local_qualified

            return func_name

        # Method call: obj.method()
        elif isinstance(func, ast.Attribute):
            # Try to resolve the full path
            try:
                full_path = ast.unparse(func)
                return full_path
            except:
                return func.attr

        return None

    def _get_qualified_name(self, filepath: str, func_name: str) -> str:
        """
        Get qualified name for a function.

        Args:
            filepath: File path
            func_name: Function name

        Returns:
            Qualified name like "module.submodule.function"
        """
        # Convert filepath to module path
        rel_path = Path(filepath).relative_to(self.project_root) if self.project_root else Path(filepath)
        module_parts = list(rel_path.parts[:-1]) + [rel_path.stem]
        module_path = ".".join(module_parts)

        return f"{module_path}.{func_name}"

    def export_graph(self) -> Dict[str, Any]:
        """Export call graph as JSON-serializable dict."""
        return {
            "nodes": {
                name: {
                    "name": node.name,
                    "filepath": node.filepath,
                    "lineno": node.lineno,
                    "calls": list(node.calls),
                    "called_by": list(node.called_by),
                    "parameters": node.parameters
                }
                for name, node in self.graph.nodes.items()
            },
            "imports": self.graph.imports,
            "file_functions": dict(self.graph.file_functions)
        }


def build_call_graph(filepaths: List[str], project_root: str = ".") -> CallGraph:
    """
    Build call graph from list of files.

    Args:
        filepaths: List of Python file paths
        project_root: Project root directory

    Returns:
        CallGraph object
    """
    builder = CallGraphBuilder(project_root)
    return builder.build_from_files(filepaths)


if __name__ == "__main__":
    # Test call graph builder
    import sys

    if len(sys.argv) > 1:
        files = sys.argv[1:]
        graph = build_call_graph(files)

        print(f"Built call graph with {len(graph.nodes)} functions")
        print(f"Files analyzed: {len(graph.file_functions)}")

        # Show some statistics
        total_calls = sum(len(node.calls) for node in graph.nodes.values())
        print(f"Total function calls: {total_calls}")
    else:
        print("Usage: python call_graph.py <file1.py> <file2.py> ...")
