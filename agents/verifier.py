"""
Stage 4: Verification
Verify vulnerabilities against CWE database and generate attack trees.
"""

import json
from typing import Dict, List, Any
from pathlib import Path

from tools.cwe_database import verify_against_cwe
from tools.attack_tree_builder import build_attack_tree


def run_stage4(debate_results: Dict[str, Any], consensus_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Stage 4: Single-pass verification.
    
    Args:
        debate_results: Results from Stage 3 debate
        consensus_results: Original consensus results (for filepath info)
    
    Returns:
        List of verified vulnerabilities with CWE info and attack trees
    """
    # Check cache
    cache_file = Path('cache/stage4_verified.json')
    if cache_file.exists():
        print("✓ Stage 4 cache found, loading...")
        with open(cache_file) as f:
            return json.load(f)
    
    print("\nStage 4: Verification & Attack Trees")
    print("=" * 50)
    
    # Check if debate was skipped
    if debate_results.get('skipped'):
        print("No vulnerabilities to verify - skipping")
        result = []
        
        cache_file.parent.mkdir(exist_ok=True)
        with open(cache_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        return result
    
    vulnerabilities = debate_results.get('vulnerabilities', [])
    print(f"Verifying {len(vulnerabilities)} vulnerabilities")
    
    # Verify each vulnerability against CWE database
    verified_vulns = []
    
    for vuln in vulnerabilities:
        verified = verify_against_cwe(vuln)
        verified_vulns.append(verified)
        
        if verified.get('cwe_verified'):
            print(f"  ✓ {vuln['type']} verified against {vuln.get('cwe_id', 'CWE')}")
        else:
            print(f"  ⚠ {vuln['type']} - no CWE match")
    
    # Group vulnerabilities by file
    by_file = {}
    for vuln in verified_vulns:
        location = vuln.get('location', 'unknown')
        filepath = location.split(':')[0] if ':' in location else 'unknown'
        
        if filepath not in by_file:
            by_file[filepath] = []
        by_file[filepath].append(vuln)
    
    # Generate attack trees for each file
    results = []
    
    for filepath, file_vulns in by_file.items():
        print(f"\n  Generating attack tree for {filepath}")
        attack_tree = build_attack_tree(file_vulns, filepath)
        
        if attack_tree:
            print(f"    ✓ {attack_tree['total_paths']} attack paths identified")
            print(f"    ✓ Highest severity: {attack_tree['highest_severity']}")
        
        results.append({
            'filepath': filepath,
            'vulnerabilities': file_vulns,
            'attack_tree': attack_tree,
            'total_vulns': len(file_vulns)
        })
    
    # Cache results
    cache_file.parent.mkdir(exist_ok=True)
    with open(cache_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ Stage 4 complete - cached to {cache_file}")
    
    return results


if __name__ == "__main__":
    # Test Stage 4
    from agents.code_parser import run_stage1
    from agents.security_agents import run_stage2
    from agents.debate_room import run_stage3
    
    print("Running Stages 1-3...")
    extractions = run_stage1()
    consensus = run_stage2(extractions)
    debate = run_stage3(consensus)
    
    print("\nRunning Stage 4...")
    verified = run_stage4(debate, consensus)
    
    print(f"\n✓ Verified {sum(r['total_vulns'] for r in verified)} vulnerabilities")
    
    for result in verified:
        if result.get('attack_tree'):
            tree = result['attack_tree']
            print(f"\nAttack tree for {result['filepath']}:")
            print(f"  Root goal: {tree['root_goal']}")
            print(f"  Attack paths: {tree['total_paths']}")
