"""
Attack Tree Builder
Generates attack trees showing exploitation paths (single-file scope).
"""

from typing import Dict, List, Any


def build_attack_tree(vulnerabilities: List[Dict[str, Any]], filepath: str) -> Dict[str, Any]:
    """
    Build attack tree for vulnerabilities in a single file.
    
    Args:
        vulnerabilities: List of verified vulnerabilities
        filepath: File being analyzed
    
    Returns:
        Attack tree structure
    """
    if not vulnerabilities:
        return None
    
    # Determine root goal based on vulnerability types
    vuln_types = set(v['type'] for v in vulnerabilities)
    
    if 'SQL_INJECTION' in vuln_types or 'COMMAND_INJECTION' in vuln_types:
        root_goal = "Compromise system via code execution"
    elif 'XSS' in vuln_types:
        root_goal = "Steal user credentials or session"
    elif 'PATH_TRAVERSAL' in vuln_types:
        root_goal = "Access sensitive files"
    else:
        root_goal = "Exploit application vulnerabilities"
    
    # Build attack paths
    attack_paths = []
    
    for vuln in vulnerabilities:
        path = _build_attack_path(vuln)
        attack_paths.append(path)
    
    # Identify critical functions (functions with multiple vulns)
    location_counts = {}
    for vuln in vulnerabilities:
        loc = vuln.get('location', 'unknown')
        location_counts[loc] = location_counts.get(loc, 0) + 1
    
    critical_locations = [loc for loc, count in location_counts.items() if count > 1]
    
    return {
        "file": filepath,
        "root_goal": root_goal,
        "attack_paths": attack_paths,
        "critical_locations": critical_locations,
        "total_paths": len(attack_paths),
        "highest_severity": _get_highest_severity(vulnerabilities)
    }


def _build_attack_path(vuln: Dict[str, Any]) -> Dict[str, Any]:
    """Build attack path for a single vulnerability."""
    vuln_type = vuln['type']
    location = vuln.get('location', 'unknown')
    severity = vuln.get('debated_severity', vuln.get('severity', 'MEDIUM'))
    
    # Define attack steps based on vulnerability type
    steps_map = {
        'SQL_INJECTION': [
            f"1. Identify SQL injection at {location}",
            "2. Craft malicious SQL payload (e.g., ' OR '1'='1)",
            "3. Bypass authentication or extract data",
            "4. Escalate to full database access"
        ],
        'XSS': [
            f"1. Identify XSS vulnerability at {location}",
            "2. Inject malicious JavaScript payload",
            "3. Steal session cookies or credentials",
            "4. Hijack user account"
        ],
        'PATH_TRAVERSAL': [
            f"1. Identify path traversal at {location}",
            "2. Craft path with ../ sequences",
            "3. Access sensitive files (e.g., /etc/passwd)",
            "4. Exfiltrate configuration or credentials"
        ],
        'COMMAND_INJECTION': [
            f"1. Identify command injection at {location}",
            "2. Inject shell metacharacters (e.g., ; whoami)",
            "3. Execute arbitrary system commands",
            "4. Establish persistent backdoor"
        ],
        'MISSING_INPUT_VALIDATION': [
            f"1. Identify unvalidated input at {location}",
            "2. Send malformed or oversized input",
            "3. Trigger unexpected behavior or crash",
            "4. Exploit resulting vulnerability"
        ]
    }
    
    steps = steps_map.get(vuln_type, [
        f"1. Identify {vuln_type} at {location}",
        "2. Craft exploit payload",
        "3. Execute attack",
        "4. Achieve compromise"
    ])
    
    # Determine difficulty and time
    difficulty_map = {
        'CRITICAL': 'EASY',
        'HIGH': 'MEDIUM',
        'MEDIUM': 'MEDIUM',
        'LOW': 'HARD'
    }
    
    time_map = {
        'CRITICAL': '5-15 minutes',
        'HIGH': '15-30 minutes',
        'MEDIUM': '30-60 minutes',
        'LOW': '1-2 hours'
    }
    
    return {
        "vulnerability": vuln_type,
        "location": location,
        "severity": severity,
        "steps": steps,
        "difficulty": difficulty_map.get(severity, 'MEDIUM'),
        "time_to_exploit": time_map.get(severity, '30-60 minutes'),
        "impact": _get_impact(vuln_type)
    }


def _get_impact(vuln_type: str) -> str:
    """Get impact description for vulnerability type."""
    impact_map = {
        'SQL_INJECTION': 'Full database compromise, data exfiltration',
        'XSS': 'Session hijacking, credential theft',
        'PATH_TRAVERSAL': 'Arbitrary file read, configuration exposure',
        'COMMAND_INJECTION': 'Remote code execution, full system compromise',
        'MISSING_INPUT_VALIDATION': 'Application crash, potential exploitation'
    }
    return impact_map.get(vuln_type, 'System compromise')


def _get_highest_severity(vulnerabilities: List[Dict[str, Any]]) -> str:
    """Get highest severity from list of vulnerabilities."""
    severity_order = {'CRITICAL': 4, 'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}
    severities = [v.get('debated_severity', v.get('severity', 'LOW')) for v in vulnerabilities]
    return max(severities, key=lambda s: severity_order.get(s, 0))
