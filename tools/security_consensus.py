"""
Security-specific consensus scoring.
Matches vulnerabilities across agents by location and type.
"""

from typing import Dict, List, Any
from collections import defaultdict


def score_security_consensus(
    agent_a_result: Dict[str, Any],
    agent_b_result: Dict[str, Any],
    agent_c_result: Dict[str, Any],
    filepath: str
) -> Dict[str, Any]:
    """
    Score consensus across 3 security agents.

    Args:
        agent_a_result: Static analysis results (Gemini)
        agent_b_result: Adversarial results (Groq)
        agent_c_result: Defensive results (Claude)
        filepath: File being analyzed

    Returns:
        Consensus report with vulnerabilities tagged by confidence
    """
    # Extract vulnerabilities from each agent
    agent_a_vulns = agent_a_result.get('vulnerabilities', [])
    agent_b_vulns = agent_b_result.get('vulnerabilities', [])
    agent_c_vulns = agent_c_result.get('vulnerabilities', [])

    # Check if any agents failed
    active_agents = 3
    if agent_a_result.get('error') == 'gemini_unavailable':
        active_agents = 2
        print("    Using 2-agent consensus (Gemini unavailable)")

    # Adjust threshold based on active agents
    consensus_threshold = 2 if active_agents == 3 else 1  # 2/3 or 1/2

    # Tag each vuln with its source
    for vuln in agent_a_vulns:
        vuln['source'] = 'agent_a'
    for vuln in agent_b_vulns:
        vuln['source'] = 'agent_b'
    for vuln in agent_c_vulns:
        vuln['source'] = 'agent_c'

    # Combine all vulnerabilities
    all_vulns = agent_a_vulns + agent_b_vulns + agent_c_vulns

    # Group by location + normalized type
    grouped = defaultdict(list)
    for vuln in all_vulns:
        # Create key from location and normalized type
        location = vuln.get('location', 'unknown')
        vuln_type = vuln.get('type', 'UNKNOWN').upper()
        
        # Normalize common types
        normalized_type = vuln_type
        if any(t in vuln_type for t in ['SQL_INJECTION', 'SQLI']):
            normalized_type = 'SQL_INJECTION'
        elif any(t in vuln_type for t in ['COMMAND_INJECTION', 'CMD_INJECTION', 'OS_COMMAND']):
            normalized_type = 'COMMAND_INJECTION'
        elif any(t in vuln_type for t in ['XSS', 'CROSS_SITE_SCRIPTING']):
            normalized_type = 'XSS'
        elif any(t in vuln_type for t in ['DESERIALIZATION', 'PICKLE']):
            normalized_type = 'INSECURE_DESERIALIZATION'
        elif any(t in vuln_type for t in ['PATH_TRAVERSAL', 'LFI', 'DIRECTORY_TRAVERSAL']):
            normalized_type = 'PATH_TRAVERSAL'
            
        key = f"{location}:{normalized_type}"
        grouped[key].append(vuln)

    # Score consensus (2/3 threshold)
    consensus_vulns = []

    for key, vulns in grouped.items():
        # Count unique agents that found this vuln
        sources = set(v['source'] for v in vulns)
        agent_count = len(sources)

        if agent_count >= consensus_threshold:  # Dynamic threshold
            # Use the first vuln as template, merge info from others
            primary = vulns[0]

            # Collect all descriptions
            descriptions = [v.get('description', '') for v in vulns]

            # Determine highest severity
            severities = [v.get('severity', 'LOW') for v in vulns]
            severity_order = {'CRITICAL': 4, 'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}
            max_severity = max(severities, key=lambda s: severity_order.get(s, 0))

            consensus_vulns.append({
                'type': primary.get('type'),
                'location': primary.get('location'),
                'severity': max_severity,
                'confidence': 'HIGH' if agent_count == active_agents else 'MEDIUM',
                'agent_count': f"{agent_count}/{active_agents}",
                'sources': list(sources),
                'description': descriptions[0],  # Use first agent's description
                'all_descriptions': descriptions,
                'evidence': primary.get('evidence', ''),
                'cwe_id': primary.get('cwe_id', ''),
                'blast_radius': primary.get('blast_radius', ''),
                'exploit_difficulty': primary.get('exploit_difficulty', '')
            })

    # Count by confidence level
    high_confidence = sum(1 for v in consensus_vulns if v['confidence'] == 'HIGH')
    medium_confidence = sum(1 for v in consensus_vulns if v['confidence'] == 'MEDIUM')

    return {
        'filepath': filepath,
        'total_vulns': len(consensus_vulns),
        'high_confidence': high_confidence,
        'medium_confidence': medium_confidence,
        'vulnerabilities': consensus_vulns,
        'agent_results': {
            'agent_a_count': len(agent_a_vulns),
            'agent_b_count': len(agent_b_vulns),
            'agent_c_count': len(agent_c_vulns)
        }
    }


def merge_consensus_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Merge consensus results from multiple files.

    Args:
        results: List of consensus results (one per file)

    Returns:
        Merged summary
    """
    all_vulns = []
    for result in results:
        all_vulns.extend(result.get('vulnerabilities', []))

    # Count by severity
    critical = sum(1 for v in all_vulns if v['severity'] == 'CRITICAL')
    high = sum(1 for v in all_vulns if v['severity'] == 'HIGH')
    medium = sum(1 for v in all_vulns if v['severity'] == 'MEDIUM')
    low = sum(1 for v in all_vulns if v['severity'] == 'LOW')

    # Count by confidence
    high_conf = sum(1 for v in all_vulns if v['confidence'] == 'HIGH')
    medium_conf = sum(1 for v in all_vulns if v['confidence'] == 'MEDIUM')

    return {
        'total_files': len(results),
        'total_vulnerabilities': len(all_vulns),
        'by_severity': {
            'critical': critical,
            'high': high,
            'medium': medium,
            'low': low
        },
        'by_confidence': {
            'high': high_conf,
            'medium': medium_conf
        },
        'vulnerabilities': all_vulns
    }
