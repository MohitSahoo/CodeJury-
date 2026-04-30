"""
Stage 3: Severity Debate
Debate vulnerability severity when vulns are found.
"""

import json
from typing import Dict, List, Any
from pathlib import Path


def run_stage3(consensus_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Stage 3: Severity debate (only if vulnerabilities found).

    Args:
        consensus_results: List of consensus results from Stage 2

    Returns:
        Debate results with severity rankings
    """
    # Check cache
    cache_file = Path('cache/stage3_debate.json')
    if cache_file.exists():
        print("✓ Stage 3 cache found, loading...")
        with open(cache_file) as f:
            return json.load(f)

    print("\nStage 3: Severity Debate")
    print("=" * 50)

    # Check if any vulnerabilities found
    total_vulns = sum(r['total_vulns'] for r in consensus_results)

    if total_vulns == 0:
        print("No vulnerabilities found - skipping debate")
        result = {
            "skipped": True,
            "reason": "no vulnerabilities found"
        }

        cache_file.parent.mkdir(exist_ok=True)
        with open(cache_file, 'w') as f:
            json.dump(result, f, indent=2)

        return result

    print(f"Found {total_vulns} vulnerabilities - running debate")

    # For MVP: Simple severity adjustment based on consensus
    # In production, this would run actual debate with Claude API

    debated_results = []

    for consensus in consensus_results:
        for vuln in consensus.get('vulnerabilities', []):
            # Adjust severity based on confidence
            original_severity = vuln['severity']
            confidence = vuln['confidence']
            agent_count = vuln.get('agent_count', '0/3')  # Already formatted as "2/3"

            # High confidence vulns keep their severity
            # Medium confidence vulns get downgraded one level
            if confidence == 'MEDIUM':
                severity_map = {
                    'CRITICAL': 'HIGH',
                    'HIGH': 'MEDIUM',
                    'MEDIUM': 'LOW',
                    'LOW': 'LOW'
                }
                adjusted_severity = severity_map.get(original_severity, original_severity)
            else:
                adjusted_severity = original_severity

            # Build detailed reasoning
            reasoning_parts = []
            reasoning_parts.append(f"Agent consensus: {agent_count} agents detected this vulnerability")
            reasoning_parts.append(f"Confidence level: {confidence}")

            if confidence == 'HIGH':
                reasoning_parts.append("All agents agree on severity - no adjustment needed")
            elif confidence == 'MEDIUM':
                reasoning_parts.append(f"Partial consensus - severity adjusted from {original_severity} to {adjusted_severity}")

            # Add exploit context if available
            exploit_difficulty = vuln.get('exploit_difficulty', '').strip()
            blast_radius = vuln.get('blast_radius', '').strip()

            if exploit_difficulty:
                reasoning_parts.append(f"Exploit difficulty: {exploit_difficulty}")
            if blast_radius:
                reasoning_parts.append(f"Blast radius: {blast_radius}")

            debated_results.append({
                'type': vuln['type'],
                'location': vuln['location'],
                'original_severity': original_severity,
                'debated_severity': adjusted_severity,
                'confidence': confidence,
                'agent_consensus': f"{agent_count} agents",
                'sources': vuln.get('sources', []),
                'all_descriptions': vuln.get('all_descriptions', []),
                'description': vuln['description'],
                'evidence': vuln['evidence'],
                'cwe_id': vuln.get('cwe_id', ''),
                'exploit_difficulty': exploit_difficulty,
                'blast_radius': blast_radius,
                'reasoning': ' | '.join(reasoning_parts),
                'debate_summary': {
                    'agents_detected': agent_count,
                    'confidence_level': confidence,
                    'severity_adjusted': adjusted_severity != original_severity,
                    'adjustment_reason': 'Partial consensus requires severity downgrade' if adjusted_severity != original_severity else 'Full consensus maintains severity'
                }
            })

    result = {
        "skipped": False,
        "total_debated": len(debated_results),
        "vulnerabilities": debated_results
    }

    # Cache
    cache_file.parent.mkdir(exist_ok=True)
    with open(cache_file, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"✓ Debated {len(debated_results)} vulnerabilities")
    print(f"✓ Stage 3 complete - cached to {cache_file}")

    return result


if __name__ == "__main__":
    # Test Stage 3
    from agents.code_parser import run_stage1
    from agents.security_agents import run_stage2

    print("Running Stages 1-2...")
    extractions = run_stage1()
    consensus = run_stage2(extractions)

    print("\nRunning Stage 3...")
    debate = run_stage3(consensus)

    if not debate.get('skipped'):
        print(f"\n✓ Debated {debate['total_debated']} vulnerabilities")
