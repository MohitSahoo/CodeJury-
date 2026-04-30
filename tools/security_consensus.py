"""
Security-specific consensus scoring.
Matches vulnerabilities across agents by location and type.
"""

import json
from typing import Dict, List, Any
from collections import defaultdict

def _normalize_type(vuln_type: str) -> str:
    vuln_type = str(vuln_type).upper()
    if any(t in vuln_type for t in ['SQL_INJECTION', 'SQLI']): return 'SQL_INJECTION'
    if any(t in vuln_type for t in ['COMMAND_INJECTION', 'CMD_INJECTION', 'OS_COMMAND']): return 'COMMAND_INJECTION'
    if any(t in vuln_type for t in ['XSS', 'CROSS_SITE_SCRIPTING']): return 'XSS'
    if any(t in vuln_type for t in ['DESERIALIZATION', 'PICKLE']): return 'INSECURE_DESERIALIZATION'
    if any(t in vuln_type for t in ['PATH_TRAVERSAL', 'LFI', 'DIRECTORY_TRAVERSAL']): return 'PATH_TRAVERSAL'
    return vuln_type

def _parse_location(location: str):
    try:
        parts = str(location).split(':')
        if len(parts) >= 2:
            filename = ':'.join(parts[:-1])
            line = int(parts[-1])
            return filename, line
        return str(location), 0
    except:
        return str(location), 0

def score_security_consensus(
    agent_a_result: Dict[str, Any],
    agent_b_result: Dict[str, Any],
    agent_c_result: Dict[str, Any],
    filepath: str
) -> Dict[str, Any]:
    """
    Score consensus across security agents with graceful degradation.
    - 3 agents: need 2/3 consensus (66%)
    - 2 agents: need 2/2 consensus (100%)
    - 1 agent: insufficient for consensus
    """
    # Extract vulnerabilities
    agent_a_vulns = agent_a_result.get('vulnerabilities', [])
    agent_b_vulns = agent_b_result.get('vulnerabilities', [])
    agent_c_vulns = agent_c_result.get('vulnerabilities', [])

    # Check for errors/availability
    failed_agents = []
    if not agent_a_vulns and agent_a_result.get('error'):
        failed_agents.append('agent_a')
    if not agent_b_vulns and agent_b_result.get('error'):
        failed_agents.append('agent_b')
    if not agent_c_vulns and agent_c_result.get('error'):
        failed_agents.append('agent_c')

    active_agents_count = 3 - len(failed_agents)

    # Consensus threshold: always need 2 agents to agree
    # 3 agents: 2/3 = 66%
    # 2 agents: 2/2 = 100%
    # 1 agent: insufficient
    consensus_threshold = 2

    if active_agents_count < 2:
        raise ValueError(f"Insufficient agents for consensus: only {active_agents_count} active, need at least 2")

    if len(failed_agents) > 0:
        print(f"    ⚠ Using {active_agents_count}-agent consensus ({', '.join(failed_agents)} failed/skipped)")

    # Tag each vuln with its source
    for vuln in agent_a_vulns: vuln['source'] = 'agent_a'
    for vuln in agent_b_vulns: vuln['source'] = 'agent_b'
    for vuln in agent_c_vulns: vuln['source'] = 'agent_c'

    all_vulns = agent_a_vulns + agent_b_vulns + agent_c_vulns
    
    # Fuzzy grouping by normalized type and line range
    consensus_vulns = []
    processed_indices = set()

    for i, v1 in enumerate(all_vulns):
        if i in processed_indices:
            continue
            
        group = [v1]
        processed_indices.add(i)
        
        v1_type = _normalize_type(v1.get('type', ''))
        v1_file, v1_line = _parse_location(v1.get('location', ''))
        
        # Look for matches in remaining vulns
        for j, v2 in enumerate(all_vulns):
            if j in processed_indices:
                continue
            
            v2_type = _normalize_type(v2.get('type', ''))
            v2_file, v2_line = _parse_location(v2.get('location', ''))
            
            # Match if type is same and line is within +/- 2 lines
            if v1_type == v2_type and v1_file == v2_file:
                if abs(v1_line - v2_line) <= 2:
                    group.append(v2)
                    processed_indices.add(j)
        
        # Check if group meets threshold
        sources = set(v['source'] for v in group)
        if len(sources) >= consensus_threshold:
            primary = group[0]
            descriptions = [v.get('description', '') for v in group]
            severities = [v.get('severity', 'LOW') for v in group]
            severity_order = {'CRITICAL': 4, 'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}
            max_severity = max(severities, key=lambda s: severity_order.get(s, 0))
            
            consensus_vulns.append({
                'type': v1_type,
                'location': primary.get('location'),
                'severity': max_severity,
                'confidence': 'HIGH' if len(sources) == active_agents_count else 'MEDIUM',
                'agent_count': f"{len(sources)}/{active_agents_count}",
                'sources': list(sources),
                'description': descriptions[0],
                'all_descriptions': descriptions,
                'evidence': primary.get('evidence', ''),
                'cwe_id': primary.get('cwe_id', ''),
            })

    return {
        'filepath': filepath,
        'total_vulns': len(consensus_vulns),
        'high_confidence': sum(1 for v in consensus_vulns if v['confidence'] == 'HIGH'),
        'medium_confidence': sum(1 for v in consensus_vulns if v['confidence'] == 'MEDIUM'),
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
    """
    all_vulns = []
    for result in results:
        all_vulns.extend(result.get('vulnerabilities', []))

    # Count by severity
    critical = sum(1 for v in all_vulns if v['severity'] == 'CRITICAL')
    high = sum(1 for v in all_vulns if v['severity'] == 'HIGH')
    medium = sum(1 for v in all_vulns if v['severity'] == 'MEDIUM')
    low = sum(1 for v in all_vulns if v['severity'] == 'LOW')

    return {
        'total_files': len(results),
        'total_vulnerabilities': len(all_vulns),
        'by_severity': {
            'critical': critical,
            'high': high,
            'medium': medium,
            'low': low
        },
        'vulnerabilities': all_vulns
    }
