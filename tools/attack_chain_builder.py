"""
Cross-File Attack Chain Builder
Identifies multi-step attack chains spanning multiple files.
"""

from typing import Dict, List, Any, Set, Tuple
from collections import defaultdict

from tools.call_graph import CallGraph
from tools.cross_file_taint import TaintFlow


class AttackStep:
    """Represents a single step in an attack chain."""

    def __init__(
        self,
        step_number: int,
        vulnerability_type: str,
        location: str,
        description: str,
        severity: str
    ):
        self.step_number = step_number
        self.vulnerability_type = vulnerability_type
        self.location = location
        self.description = description
        self.severity = severity
        self.enables: List[str] = []  # What this step enables

    def __repr__(self):
        return f"<AttackStep {self.step_number}: {self.vulnerability_type} at {self.location}>"


class AttackChain:
    """Represents a multi-step attack chain across files."""

    def __init__(self, chain_id: str, root_goal: str):
        self.chain_id = chain_id
        self.root_goal = root_goal
        self.steps: List[AttackStep] = []
        self.files_involved: Set[str] = set()
        self.total_severity_score: int = 0
        self.difficulty: str = "MEDIUM"
        self.time_to_exploit: str = "30-60 minutes"
        self.impact: str = ""

    def add_step(self, step: AttackStep):
        """Add a step to the attack chain."""
        self.steps.append(step)
        # Extract filepath from location
        if ':' in step.location:
            filepath = step.location.split(':')[0]
            self.files_involved.add(filepath)

    def calculate_severity_score(self) -> int:
        """Calculate total severity score for the chain."""
        severity_map = {'CRITICAL': 10, 'HIGH': 7, 'MEDIUM': 4, 'LOW': 2}
        score = sum(severity_map.get(step.severity, 0) for step in self.steps)
        self.total_severity_score = score
        return score

    def determine_difficulty(self):
        """Determine overall difficulty based on chain complexity."""
        if len(self.steps) == 1:
            severity = self.steps[0].severity
            if severity == 'CRITICAL':
                self.difficulty = 'EASY'
            elif severity == 'HIGH':
                self.difficulty = 'MEDIUM'
            else:
                self.difficulty = 'HARD'
        elif len(self.steps) == 2:
            self.difficulty = 'MEDIUM'
        else:
            self.difficulty = 'HARD'

    def estimate_time(self):
        """Estimate time to exploit the full chain."""
        if self.difficulty == 'EASY':
            self.time_to_exploit = '5-15 minutes'
        elif self.difficulty == 'MEDIUM':
            self.time_to_exploit = '15-45 minutes'
        else:
            self.time_to_exploit = '1-3 hours'

    def __repr__(self):
        return f"<AttackChain {self.chain_id}: {len(self.steps)} steps across {len(self.files_involved)} files>"


class AttackChainBuilder:
    """Builds cross-file attack chains from vulnerabilities and taint flows."""

    def __init__(self, call_graph: CallGraph):
        self.call_graph = call_graph
        self.chains: List[AttackChain] = []

    def build_chains(
        self,
        vulnerabilities: List[Dict[str, Any]],
        taint_flows: List[TaintFlow]
    ) -> List[AttackChain]:
        """
        Build attack chains from vulnerabilities and taint flows.

        Args:
            vulnerabilities: List of verified vulnerabilities
            taint_flows: List of cross-file taint flows

        Returns:
            List of AttackChain objects
        """
        # Group vulnerabilities by file
        vulns_by_file = defaultdict(list)
        for vuln in vulnerabilities:
            location = vuln.get('location', 'unknown')
            filepath = location.split(':')[0] if ':' in location else 'unknown'
            vulns_by_file[filepath].append(vuln)

        # Build single-step chains (individual vulnerabilities)
        for filepath, file_vulns in vulns_by_file.items():
            for vuln in file_vulns:
                chain = self._build_single_step_chain(vuln)
                self.chains.append(chain)

        # Build multi-step chains from taint flows
        for flow in taint_flows:
            if len(flow.path) > 1 and flow.sinks:
                chain = self._build_taint_flow_chain(flow, vulnerabilities)
                if chain:
                    self.chains.append(chain)

        # Build chained exploitation paths (auth bypass → data access)
        self._build_chained_exploits(vulnerabilities)

        # Calculate metrics for all chains
        for chain in self.chains:
            chain.calculate_severity_score()
            chain.determine_difficulty()
            chain.estimate_time()

        # Sort by severity score (highest first)
        self.chains.sort(key=lambda c: c.total_severity_score, reverse=True)

        return self.chains

    def _build_single_step_chain(self, vuln: Dict[str, Any]) -> AttackChain:
        """Build a single-step attack chain from a vulnerability."""
        vuln_type = vuln.get('type', 'UNKNOWN')
        location = vuln.get('location', 'unknown')
        severity = vuln.get('debated_severity', vuln.get('severity', 'MEDIUM'))

        # Determine root goal
        goal_map = {
            'SQL_INJECTION': 'Compromise database via SQL injection',
            'COMMAND_INJECTION': 'Execute arbitrary commands on server',
            'XSS': 'Steal user credentials via XSS',
            'PATH_TRAVERSAL': 'Access sensitive files',
            'INSECURE_DESERIALIZATION': 'Execute arbitrary code via deserialization',
            'MISSING_INPUT_VALIDATION': 'Exploit unvalidated input'
        }
        root_goal = goal_map.get(vuln_type, f'Exploit {vuln_type}')

        chain = AttackChain(
            chain_id=f"single_{vuln_type}_{location}",
            root_goal=root_goal
        )

        step = AttackStep(
            step_number=1,
            vulnerability_type=vuln_type,
            location=location,
            description=vuln.get('description', ''),
            severity=severity
        )

        chain.add_step(step)
        chain.impact = self._get_impact(vuln_type)

        return chain

    def _build_taint_flow_chain(
        self,
        flow: TaintFlow,
        vulnerabilities: List[Dict[str, Any]]
    ) -> AttackChain:
        """Build attack chain from a taint flow."""
        chain = AttackChain(
            chain_id=f"taint_flow_{flow.source.filepath}_{flow.source.lineno}",
            root_goal="Exploit data flow from user input to dangerous sink"
        )

        # Step 1: Inject malicious input
        step1 = AttackStep(
            step_number=1,
            vulnerability_type="USER_INPUT",
            location=f"{flow.source.filepath}:{flow.source.lineno}",
            description=f"Inject malicious data via {flow.source.source_type}",
            severity="MEDIUM"
        )
        step1.enables = ["Data propagates through application"]
        chain.add_step(step1)

        # Step 2+: Follow the flow through functions
        for idx, (func, filepath, lineno) in enumerate(flow.path[1:], start=2):
            step = AttackStep(
                step_number=idx,
                vulnerability_type="DATA_FLOW",
                location=f"{filepath}:{lineno}",
                description=f"Malicious data flows through {func}",
                severity="LOW"
            )
            chain.add_step(step)

        # Final step: Exploit the sink
        for sink_type, filepath, lineno in flow.sinks:
            final_step = AttackStep(
                step_number=len(chain.steps) + 1,
                vulnerability_type=sink_type.upper(),
                location=f"{filepath}:{lineno}",
                description=f"Exploit {sink_type} with tainted data",
                severity=self._get_sink_severity(sink_type)
            )
            chain.add_step(final_step)

        chain.impact = f"Cross-file data flow exploitation via {len(flow.path)} functions"

        return chain

    def _build_chained_exploits(self, vulnerabilities: List[Dict[str, Any]]):
        """Build chains where one vulnerability enables another."""
        # Group by type
        by_type = defaultdict(list)
        for vuln in vulnerabilities:
            vuln_type = vuln.get('type', 'UNKNOWN')
            by_type[vuln_type].append(vuln)

        # Common attack chains
        chain_patterns = [
            # Auth bypass → Data access
            (['MISSING_INPUT_VALIDATION', 'AUTHENTICATION_BYPASS'], ['SQL_INJECTION', 'PATH_TRAVERSAL']),
            # XSS → Session hijack → Privilege escalation
            (['XSS'], ['AUTHENTICATION_BYPASS', 'AUTHORIZATION_BYPASS']),
            # Path traversal → Config exposure → Credential theft
            (['PATH_TRAVERSAL'], ['INSECURE_DESERIALIZATION', 'COMMAND_INJECTION']),
        ]

        for enablers, exploits in chain_patterns:
            for enabler_type in enablers:
                for exploit_type in exploits:
                    if enabler_type in by_type and exploit_type in by_type:
                        # Create chained attack
                        for enabler_vuln in by_type[enabler_type]:
                            for exploit_vuln in by_type[exploit_type]:
                                chain = self._create_chained_attack(
                                    enabler_vuln, exploit_vuln
                                )
                                self.chains.append(chain)

    def _create_chained_attack(
        self,
        enabler: Dict[str, Any],
        exploit: Dict[str, Any]
    ) -> AttackChain:
        """Create a chained attack from two vulnerabilities."""
        chain = AttackChain(
            chain_id=f"chain_{enabler['type']}_{exploit['type']}",
            root_goal=f"Chain {enabler['type']} to enable {exploit['type']}"
        )

        # Step 1: Exploit enabler
        step1 = AttackStep(
            step_number=1,
            vulnerability_type=enabler['type'],
            location=enabler.get('location', 'unknown'),
            description=f"Exploit {enabler['type']} to gain initial access",
            severity=enabler.get('debated_severity', enabler.get('severity', 'MEDIUM'))
        )
        step1.enables = [f"Enables {exploit['type']} exploitation"]
        chain.add_step(step1)

        # Step 2: Exploit the enabled vulnerability
        step2 = AttackStep(
            step_number=2,
            vulnerability_type=exploit['type'],
            location=exploit.get('location', 'unknown'),
            description=f"Use gained access to exploit {exploit['type']}",
            severity=exploit.get('debated_severity', exploit.get('severity', 'MEDIUM'))
        )
        chain.add_step(step2)

        chain.impact = f"Chained exploitation: {enabler['type']} → {exploit['type']}"

        return chain

    def _get_impact(self, vuln_type: str) -> str:
        """Get impact description for vulnerability type."""
        impact_map = {
            'SQL_INJECTION': 'Full database compromise, data exfiltration',
            'XSS': 'Session hijacking, credential theft',
            'PATH_TRAVERSAL': 'Arbitrary file read, configuration exposure',
            'COMMAND_INJECTION': 'Remote code execution, full system compromise',
            'INSECURE_DESERIALIZATION': 'Remote code execution',
            'MISSING_INPUT_VALIDATION': 'Application crash, potential exploitation'
        }
        return impact_map.get(vuln_type, 'System compromise')

    def _get_sink_severity(self, sink_type: str) -> str:
        """Get severity for a sink type."""
        severity_map = {
            'sql': 'CRITICAL',
            'command': 'CRITICAL',
            'eval': 'CRITICAL',
            'pickle': 'CRITICAL',
            'file': 'HIGH'
        }
        return severity_map.get(sink_type, 'MEDIUM')

    def export_chains(self) -> Dict[str, Any]:
        """Export attack chains as JSON-serializable dict."""
        return {
            "total_chains": len(self.chains),
            "chains": [
                {
                    "chain_id": chain.chain_id,
                    "root_goal": chain.root_goal,
                    "steps": [
                        {
                            "step": step.step_number,
                            "type": step.vulnerability_type,
                            "location": step.location,
                            "description": step.description,
                            "severity": step.severity,
                            "enables": step.enables
                        }
                        for step in chain.steps
                    ],
                    "files_involved": list(chain.files_involved),
                    "total_steps": len(chain.steps),
                    "severity_score": chain.total_severity_score,
                    "difficulty": chain.difficulty,
                    "time_to_exploit": chain.time_to_exploit,
                    "impact": chain.impact
                }
                for chain in self.chains
            ]
        }


def build_attack_chains(
    vulnerabilities: List[Dict[str, Any]],
    taint_flows: List[TaintFlow],
    call_graph: CallGraph
) -> List[AttackChain]:
    """
    Build cross-file attack chains.

    Args:
        vulnerabilities: List of verified vulnerabilities
        taint_flows: List of cross-file taint flows
        call_graph: Project call graph

    Returns:
        List of AttackChain objects
    """
    builder = AttackChainBuilder(call_graph)
    chains = builder.build_chains(vulnerabilities, taint_flows)
    return chains


if __name__ == "__main__":
    print("Attack Chain Builder - use via orchestrator")
