"""
Stage 5: Terminal Report
Rich terminal UI for vulnerability reporting.
"""

import json
from typing import Dict, List, Any, Optional

from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree
from rich import box

console = Console()


def run_stage5(verified_results: List[Dict[str, Any]], config: Optional[Dict] = None) -> int:
    """
    Stage 5: Terminal report with Rich UI or JSON output.

    Args:
        verified_results: List of verified results from Stage 4
        config: Configuration dict with output and exit code options

    Returns:
        Exit code (0=clean, 1=vulns found based on config, 2=error)
    """
    if config is None:
        config = {'json_output': False, 'fail_on_critical': True}

    # Count vulnerabilities by severity
    all_vulns = []
    for result in verified_results:
        all_vulns.extend(result.get('vulnerabilities', []))

    # Count by severity (fallback to 'severity' if 'debated_severity' not present - for quick mode)
    critical = sum(1 for v in all_vulns if v.get('debated_severity', v.get('severity')) == 'CRITICAL')
    high = sum(1 for v in all_vulns if v.get('debated_severity', v.get('severity')) == 'HIGH')
    medium = sum(1 for v in all_vulns if v.get('debated_severity', v.get('severity')) == 'MEDIUM')
    low = sum(1 for v in all_vulns if v.get('debated_severity', v.get('severity')) == 'LOW')

    # JSON output mode
    if config.get('json_output'):
        output = {
            'summary': {
                'total': len(all_vulns),
                'critical': critical,
                'high': high,
                'medium': medium,
                'low': low
            },
            'vulnerabilities': []
        }

        for result in verified_results:
            for vuln in result.get('vulnerabilities', []):
                vuln_data = {
                    'file': result['filepath'],
                    'type': vuln.get('type'),
                    'location': vuln.get('location'),
                    'severity': vuln.get('debated_severity', vuln.get('severity')),
                    'confidence': vuln.get('confidence'),
                    'description': vuln.get('description'),
                    'evidence': vuln.get('evidence'),
                    'cwe_id': vuln.get('cwe_id'),
                    'mitigation': vuln.get('mitigation'),
                }
                output['vulnerabilities'].append(vuln_data)

        print(json.dumps(output, indent=2))
        return _determine_exit_code(critical, high, medium, low, config)

    # SARIF output mode
    if config.get('sarif_output'):
        from tools.sarif_generator import save_sarif
        output_file = config.get('sarif_file', 'security-results.sarif')
        save_sarif(verified_results, output_file)
        if not config.get('summary_only'):
            console.print(f"\n[green]✓ SARIF report saved to {output_file}[/green]")
        if config.get('sarif_only', False):
            return _determine_exit_code(critical, high, medium, low, config)

    # Rich terminal output mode
    print("\nStage 5: Terminal Report")
    print("=" * 50)

    if not all_vulns:
        console.print(Panel(
            "[green]✓ No vulnerabilities found[/green]",
            title="Security Audit Complete",
            border_style="green"
        ))
        return 0

    # Summary only mode
    if config.get('summary_only'):
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
        return _determine_exit_code(critical, high, medium, low, config)

    # Full output mode
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

    # Determine exit code and print message
    exit_code = _determine_exit_code(critical, high, medium, low, config)

    if exit_code == 1:
        console.print("\n[red bold]❌ COMMIT BLOCKED - Vulnerabilities exceed threshold[/red bold]")
    else:
        console.print("\n[yellow]⚠ Vulnerabilities found but allowing commit[/yellow]")
        console.print("[dim]Run security audit again after fixes[/dim]")

    return exit_code


def _determine_exit_code(critical: int, high: int, medium: int, low: int, config: Dict) -> int:
    """
    Determine exit code based on severity counts and config.

    Args:
        critical: Count of critical vulnerabilities
        high: Count of high vulnerabilities
        medium: Count of medium vulnerabilities
        low: Count of low vulnerabilities
        config: Configuration dict

    Returns:
        Exit code (0=pass, 1=fail)
    """
    # Warn only mode - never fail
    if config.get('warn_only'):
        return 0

    # Strict mode - fail on any vulnerability
    if config.get('strict_mode'):
        if critical > 0 or high > 0 or medium > 0 or low > 0:
            return 1
        return 0

    # Fail on high or critical
    if config.get('fail_on_high'):
        if critical > 0 or high > 0:
            return 1
        return 0

    # Default: fail on critical only
    if critical > 0:
        return 1

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
        content += f"\n[green]Mitigation:[/green]\n{mitigation}\n"

    # Add detailed Agent Debate section
    debate_summary = vuln.get('debate_summary', {})
    agent_consensus = vuln.get('agent_consensus', '')
    sources = vuln.get('sources', [])
    all_descriptions = vuln.get('all_descriptions', [])

    if debate_summary or agent_consensus:
        content += f"\n[bold magenta]━━━ Agent Debate ━━━[/bold magenta]\n"

        # Show which agents detected it
        if agent_consensus:
            content += f"[cyan]Consensus:[/cyan] {agent_consensus}\n"

        # Show individual agent perspectives
        if sources and all_descriptions:
            agent_names = {
                'agent_a': 'Agent A (Static Analysis)',
                'agent_b': 'Agent B (Adversarial)',
                'agent_c': 'Agent C (Defensive)'
            }
            content += f"\n[dim]Agent Perspectives:[/dim]\n"
            for source, desc in zip(sources, all_descriptions):
                agent_name = agent_names.get(source, source)
                content += f"  • [cyan]{agent_name}:[/cyan] {desc}\n"

        # Show debate outcome
        if debate_summary:
            severity_adjusted = debate_summary.get('severity_adjusted', False)
            adjustment_reason = debate_summary.get('adjustment_reason', '')

            if severity_adjusted:
                content += f"\n[yellow]⚖️  Severity Adjusted:[/yellow] {adjustment_reason}\n"
            else:
                content += f"\n[green]✓ Severity Maintained:[/green] {adjustment_reason}\n"
    
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
