"""
Cross-File Taint Tracking
Tracks user input data flow across module boundaries.
"""

import ast
from pathlib import Path
from typing import Dict, List, Set, Any, Tuple
from collections import defaultdict

from tools.call_graph import CallGraph, build_call_graph


class TaintSource:
    """Represents a source of tainted data."""

    def __init__(self, variable: str, source_type: str, filepath: str, lineno: int):
        self.variable = variable
        self.source_type = source_type  # 'request.args', 'input()', etc.
        self.filepath = filepath
        self.lineno = lineno

    def __repr__(self):
        return f"<TaintSource {self.variable} from {self.source_type} at {self.filepath}:{self.lineno}>"


class TaintFlow:
    """Represents a taint propagation path."""

    def __init__(self, source: TaintSource):
        self.source = source
        self.path: List[Tuple[str, str, int]] = []  # (function, filepath, lineno)
        self.sinks: List[Tuple[str, str, int]] = []  # Dangerous operations

    def add_step(self, function: str, filepath: str, lineno: int):
        """Add a step in the taint flow."""
        self.path.append((function, filepath, lineno))

    def add_sink(self, sink_type: str, filepath: str, lineno: int):
        """Add a sink (dangerous operation) for this taint."""
        self.sinks.append((sink_type, filepath, lineno))

    def __repr__(self):
        return f"<TaintFlow from {self.source.source_type} through {len(self.path)} steps to {len(self.sinks)} sinks>"


class CrossFileTaintAnalyzer:
    """Analyzes taint propagation across multiple files."""

    def __init__(self, call_graph: CallGraph):
        self.call_graph = call_graph
        self.taint_sources: Dict[str, List[TaintSource]] = defaultdict(list)  # function -> sources
        self.tainted_returns: Set[str] = set()  # Functions that return tainted data
        self.tainted_params: Dict[str, Set[int]] = defaultdict(set)  # function -> param indices
        self.dangerous_sinks = {
            'sql': ['execute', 'executemany', 'raw', 'cursor.execute'],
            'command': ['subprocess.run', 'subprocess.call', 'subprocess.Popen', 'os.system', 'os.popen'],
            'file': ['open', 'Path', 'os.path.join'],
            'eval': ['eval', 'exec', '__import__'],
            'pickle': ['pickle.loads', 'pickle.load']
        }

    def analyze_files(self, filepaths: List[str]) -> List[TaintFlow]:
        """
        Analyze taint propagation across files.

        Args:
            filepaths: List of Python files to analyze

        Returns:
            List of TaintFlow objects showing taint propagation
        """
        # Phase 1: Identify taint sources in each file
        for filepath in filepaths:
            self._identify_taint_sources(filepath)

        # Phase 2: Propagate taint through function calls
        self._propagate_taint()

        # Phase 3: Find taint flows to dangerous sinks
        flows = self._find_taint_flows(filepaths)

        return flows

    def _identify_taint_sources(self, filepath: str):
        """Identify taint sources (user inputs) in a file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            tree = ast.parse(content, filename=filepath)
        except (SyntaxError, FileNotFoundError, UnicodeDecodeError):
            return

        user_input_patterns = [
            'request.args', 'request.form', 'request.json', 'request.data',
            'request.files', 'request.values', 'input(', 'sys.argv'
        ]

        current_function = None

        for node in ast.walk(tree):
            # Track function context
            if isinstance(node, ast.FunctionDef):
                current_function = node.name

            # Find assignments from user input
            if isinstance(node, ast.Assign) and current_function:
                rhs_str = ast.unparse(node.value)

                for pattern in user_input_patterns:
                    if pattern in rhs_str:
                        # Extract variable names
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                source = TaintSource(
                                    variable=target.id,
                                    source_type=pattern,
                                    filepath=filepath,
                                    lineno=node.lineno
                                )
                                qualified_func = self._get_qualified_function(filepath, current_function)
                                self.taint_sources[qualified_func].append(source)

    def _propagate_taint(self):
        """Propagate taint through function calls using call graph."""
        changed = True
        iterations = 0
        max_iterations = 10

        while changed and iterations < max_iterations:
            changed = False
            iterations += 1

            # For each function with taint sources
            for func_name, sources in list(self.taint_sources.items()):
                if func_name not in self.call_graph.nodes:
                    continue

                node = self.call_graph.nodes[func_name]

                # Check if function returns tainted data
                if self._function_returns_tainted(node.filepath, node.name, sources):
                    if func_name not in self.tainted_returns:
                        self.tainted_returns.add(func_name)
                        changed = True

                # Propagate to callees
                for callee in node.calls:
                    if callee in self.call_graph.nodes:
                        callee_node = self.call_graph.nodes[callee]

                        # Check if tainted data is passed as argument
                        tainted_args = self._find_tainted_arguments(
                            node.filepath, node.name, callee, sources
                        )

                        if tainted_args:
                            for arg_idx in tainted_args:
                                if arg_idx not in self.tainted_params[callee]:
                                    self.tainted_params[callee].add(arg_idx)
                                    changed = True

                                    # Create synthetic taint source for the parameter
                                    if callee_node.parameters and arg_idx < len(callee_node.parameters):
                                        param_name = callee_node.parameters[arg_idx]
                                        synthetic_source = TaintSource(
                                            variable=param_name,
                                            source_type=f"parameter from {func_name}",
                                            filepath=callee_node.filepath,
                                            lineno=callee_node.lineno
                                        )
                                        self.taint_sources[callee].append(synthetic_source)

            # Propagate from functions that return tainted data
            for func_name in list(self.tainted_returns):
                if func_name not in self.call_graph.nodes:
                    continue

                # Find all callers
                callers = self.call_graph.get_callers(func_name)
                for caller in callers:
                    if caller in self.call_graph.nodes:
                        caller_node = self.call_graph.nodes[caller]

                        # Create synthetic taint source in caller
                        synthetic_source = TaintSource(
                            variable=f"return_from_{func_name}",
                            source_type=f"return value from {func_name}",
                            filepath=caller_node.filepath,
                            lineno=caller_node.lineno
                        )

                        if synthetic_source not in self.taint_sources[caller]:
                            self.taint_sources[caller].append(synthetic_source)
                            changed = True

    def _function_returns_tainted(self, filepath: str, func_name: str, sources: List[TaintSource]) -> bool:
        """Check if a function returns tainted data."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            tree = ast.parse(content, filename=filepath)
        except (SyntaxError, FileNotFoundError, UnicodeDecodeError):
            return False

        tainted_vars = {s.variable for s in sources}

        # Find the function definition
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == func_name:
                # Check return statements
                for child in ast.walk(node):
                    if isinstance(child, ast.Return) and child.value:
                        return_str = ast.unparse(child.value)
                        # Check if any tainted variable is in the return
                        if any(var in return_str for var in tainted_vars):
                            return True

        return False

    def _find_tainted_arguments(self, filepath: str, func_name: str, callee: str, sources: List[TaintSource]) -> Set[int]:
        """Find which argument positions receive tainted data in a call."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            tree = ast.parse(content, filename=filepath)
        except (SyntaxError, FileNotFoundError, UnicodeDecodeError):
            return set()

        tainted_vars = {s.variable for s in sources}
        tainted_args = set()

        # Find the function definition
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == func_name:
                # Find calls to the callee
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        call_target = self._get_call_target(child)
                        if callee in call_target:
                            # Check each argument
                            for idx, arg in enumerate(child.args):
                                arg_str = ast.unparse(arg)
                                if any(var in arg_str for var in tainted_vars):
                                    tainted_args.add(idx)

        return tainted_args

    def _find_taint_flows(self, _filepaths: List[str]) -> List[TaintFlow]:
        """Find complete taint flows from sources to sinks."""
        flows = []

        for func_name, sources in self.taint_sources.items():
            if func_name not in self.call_graph.nodes:
                continue

            node = self.call_graph.nodes[func_name]

            for source in sources:
                flow = TaintFlow(source)
                flow.add_step(func_name, node.filepath, node.lineno)

                # Check if this function has dangerous sinks
                sinks = self._find_sinks_in_function(node.filepath, node.name, source)
                for sink in sinks:
                    flow.add_sink(*sink)

                # Trace through call chain
                self._trace_taint_flow(func_name, flow, visited=set())

                if flow.sinks:
                    flows.append(flow)

        return flows

    def _find_sinks_in_function(self, filepath: str, func_name: str, source: TaintSource) -> List[Tuple[str, str, int]]:
        """Find dangerous sinks in a function that use tainted data."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            tree = ast.parse(content, filename=filepath)
        except (SyntaxError, FileNotFoundError, UnicodeDecodeError):
            return []

        sinks = []

        # Find the function
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == func_name:
                # Look for dangerous operations
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        call_str = ast.unparse(child)

                        # Check against dangerous sinks
                        for sink_type, patterns in self.dangerous_sinks.items():
                            for pattern in patterns:
                                if pattern in call_str:
                                    # Check if tainted variable is used
                                    if source.variable in call_str:
                                        sinks.append((sink_type, filepath, child.lineno))

        return sinks

    def _trace_taint_flow(self, func_name: str, flow: TaintFlow, visited: Set[str], depth: int = 0):
        """Recursively trace taint flow through call chain."""
        if depth > 5 or func_name in visited:
            return

        visited.add(func_name)

        if func_name not in self.call_graph.nodes:
            return

        node = self.call_graph.nodes[func_name]

        # Check callees
        for callee in node.calls:
            if callee in self.call_graph.nodes:
                callee_node = self.call_graph.nodes[callee]
                flow.add_step(callee, callee_node.filepath, callee_node.lineno)

                # Check for sinks in callee
                if callee in self.taint_sources:
                    for source in self.taint_sources[callee]:
                        sinks = self._find_sinks_in_function(
                            callee_node.filepath, callee_node.name, source
                        )
                        for sink in sinks:
                            flow.add_sink(*sink)

                # Recurse
                self._trace_taint_flow(callee, flow, visited, depth + 1)

    def _get_qualified_function(self, filepath: str, func_name: str) -> str:
        """Get qualified function name."""
        # Simplified - matches call_graph logic
        return f"{Path(filepath).stem}.{func_name}"

    def _get_call_target(self, call_node: ast.Call) -> str:
        """Get the target of a call node."""
        try:
            return ast.unparse(call_node.func)
        except:
            return ""

    def export_flows(self, flows: List[TaintFlow]) -> Dict[str, Any]:
        """Export taint flows as JSON-serializable dict."""
        return {
            "total_flows": len(flows),
            "flows": [
                {
                    "source": {
                        "variable": flow.source.variable,
                        "type": flow.source.source_type,
                        "location": f"{flow.source.filepath}:{flow.source.lineno}"
                    },
                    "path": [
                        {"function": func, "location": f"{fp}:{ln}"}
                        for func, fp, ln in flow.path
                    ],
                    "sinks": [
                        {"type": sink_type, "location": f"{fp}:{ln}"}
                        for sink_type, fp, ln in flow.sinks
                    ]
                }
                for flow in flows
            ]
        }


def analyze_cross_file_taint(filepaths: List[str], project_root: str = ".") -> List[TaintFlow]:
    """
    Analyze cross-file taint propagation.

    Args:
        filepaths: List of Python files
        project_root: Project root directory

    Returns:
        List of TaintFlow objects
    """
    # Build call graph first
    call_graph = build_call_graph(filepaths, project_root)

    # Analyze taint
    analyzer = CrossFileTaintAnalyzer(call_graph)
    flows = analyzer.analyze_files(filepaths)

    return flows


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        files = sys.argv[1:]
        flows = analyze_cross_file_taint(files)

        print(f"Found {len(flows)} taint flows")

        for i, flow in enumerate(flows, 1):
            print(f"\nFlow {i}:")
            print(f"  Source: {flow.source.source_type} at {flow.source.filepath}:{flow.source.lineno}")
            print(f"  Path length: {len(flow.path)}")
            print(f"  Sinks: {len(flow.sinks)}")
            for sink_type, fp, ln in flow.sinks:
                print(f"    - {sink_type} at {fp}:{ln}")
    else:
        print("Usage: python cross_file_taint.py <file1.py> <file2.py> ...")
