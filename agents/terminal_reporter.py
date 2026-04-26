"""
Stage 5: Terminal Report
Rich terminal UI for vulnerability reporting.
"""

import json
from typing import Dict, List, Any
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich import box

console = Console()


def run_stage5(verified_results: List[Dict[str, Any]]) -> int:
    """
    Stage 5: Terminal report with Rich UI.
    
    Args:
        verified_results: List of verified results from Stage 4
    
    Returns:
        Exit code (0=clean, 1=critical vulns found, 2=error)
    """
    print("\nStage 5: Terminal Report")
    print("=" * 50)
    
    # Count vulnerabilities by severity
    all_vulns = []
    for result in verified_results:
        all_vulns.extend(result.get('vulnerabilities', []))
    
    if not all_vulns:
        console.print(Panel(
            "[green]✓ No vulnerabilities found[/green]",
            title="Security Audit Complete",
            border_style="green"
        ))
        return 0
    
    # Count by severity
    critical = sum(1 for v in all_vulns if v.get('debated_severity') == 'CRITICAL')
    high = sum(1 for v in all_vulns if v.get('debated_severity') == 'HIGH')
    medium = sum(1 for v in all_vulns if v.get('debated_severity') == 'MEDIUM')
    low = sum(1 for v in all_vulns if v.get('debated_severity') == 'LOW')
    
    # Print summary
    console.print()
    console.print(Panel(
        f"[red]⚠ {len(all_vulns)} vulnerabilities found[/red]\n\n"
        f"[red]Critical: {critical}[/red]  "
        f"[orange1]High: {high}[/orange1]  "
        f"[yellow]Medium: {medium}[/yellow]  "
        f"[blue]Low: {low}[/blue]",
        title="Security Audit Results",
        border_style="red" if critical > 0 else "yellow"
    ))
    
    # Print each vulnerability
    for result in verified_results:
        filepath = result['filepath']
        vulns = result.get('vulnerabilities', [])
        
        if not vulns:
            continue
        
        console.print(f"\n[bold cyan]File: {filepath}[/bold cyan]")
        
        for vuln in vulns:
            _print_vulnerability(vuln)
        
        # Print attack tree if available
        attack_tree = result.get('attack_tree')
        if attack_tree:
            _print_attack_tree(attack_tree)
    
    # Determine exit code
    if critical > 0:
        console.print("\n[red bold]❌ COMMIT BLOCKED - Critical vulnerabilities found[/red bold]")
        return 1
    else:
        console.print("\n[yellow]⚠ Vulnerabilities found but allowing commit[/yellow]")
        console.print("[dim]Run security audit again after fixes[/dim]")
        return 0


def _print_vulnerability(vuln: Dict[str, Any]) -> None:
    """Print single vulnerability with details."""
    vuln_type = vuln['type']
    location = vuln.get('location', 'unknown')
    severity = vuln.get('debated_severity', vuln.get('severity', 'MEDIUM'))
    confidence = vuln.get('confidence', 'MEDIUM')
    description = vuln.get('description', 'No description')
    evidence = vuln.get('evidence', '')
    cwe_id = vuln.get('cwe_id', '')
    mitigation = vuln.get('mitigation', '')
    
    # Severity colors
    severity_colors = {
        'CRITICAL': 'red',
        'HIGH': 'orange1',
        'MEDIUM': 'yellow',
        'LOW': 'blue'
    }
    color = severity_colors.get(severity, 'white')
    
    # Build panel content
    content = f"[{color}]{vuln_type}[/{color}]\n"
    content += f"Location: [cyan]{location}[/cyan]\n"
    content += f"Severity: [{color}]{severity}[/{color}] (Confidence: {confidence})\n"
    
    if cwe_id:
        content += f"CWE: [dim]{cwe_id}[/dim]\n"
    
    content += f"\n{description}\n"
    
    if evidence:
        content += f"\n[dim]Evidence:[/dim]\n[dim]{evidence[:100]}...[/dim]\n"
    
    if mitigation:
        content += f"\n[green]Mitigation:[/green]\n{mitigation}"
    
    console.print(Panel(
        content,
        title=f"[{color}]Vulnerability[/{color}]",
        border_style=color,
        box=box.ROUNDED
    ))


def _print_attack_tree(attack_tree: Dict[str, Any]) -> None:
    """Print attack tree visualization."""
    console.print("\n[bold]Attack Tree:[/bold]")
    
    tree = Tree(f"🎯 [bold]{attack_tree['root_goal']}[/bold]")
    
    for path in attack_tree.get('attack_paths', []):
        vuln_type = path['vulnerability']
        severity = path['severity']
        difficulty = path['difficulty']
        
        # Color by severity
        severity_colors = {
            'CRITICAL': 'red',
            'HIGH': 'orange1',
            'MEDIUM': 'yellow',
            'LOW': 'blue'
        }
        color = severity_colors.get(severity, 'white')
        
        branch = tree.add(
            f"[{color}]{vuln_type}[/{color}] "
            f"([dim]{difficulty} difficulty, {path['time_to_exploit']}[/dim])"
        )
        
        for step in path['steps']:
            branch.add(f"[dim]{step}[/dim]")
        
        branch.add(f"[red]Impact: {path['impact']}[/red]")
    
    console.print(tree)
    console.print()


if __name__ == "__main__":
    # Test Stage 5
    from agents.code_parser import run_stage1
    from agents.security_agents import run_stage2
    from agents.debate_room import run_stage3
    from agents.verifier import run_stage4
    
    print("Running Stages 1-4...")
    extractions = run_stage1()
    consensus = run_stage2(extractions)
    debate = run_stage3(consensus)
    verified = run_stage4(debate, consensus)
    
    print("\nRunning Stage 5...")
    exit_code = run_stage5(verified)
    
    print(f"\nExit code: {exit_code}")
