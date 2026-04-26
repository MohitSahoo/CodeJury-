"""
Main Orchestrator
Runs all 5 stages of the security audit pipeline.
"""

import sys
from pathlib import Path

from rich.console import Console

from tools.git_diff_extractor import get_staged_python_files, is_git_repository
from agents.code_parser import run_stage1
from agents.security_agents import run_stage2
from agents.debate_room import run_stage3
from agents.verifier import run_stage4
from agents.terminal_reporter import run_stage5

console = Console()


def run_security_audit() -> int:
    """
    Main orchestrator - runs all 5 stages.
    
    Returns:
        Exit code (0=clean, 1=vulns found, 2=error)
    """
    try:
        console.print("\n[bold cyan]Security Audit Pipeline[/bold cyan]")
        console.print("[dim]Multi-agent security analysis for Python code[/dim]\n")
        
        # Check if in git repository
        if not is_git_repository():
            console.print("[red]Error: Not a git repository[/red]")
            console.print("This tool must be run inside a git repository")
            return 2
        
        # Check for staged files
        staged_files = get_staged_python_files()
        if not staged_files:
            console.print("[yellow]No Python files staged[/yellow]")
            console.print("Stage some Python files with: git add <file>")
            return 0
        
        console.print(f"[green]✓[/green] Found {len(staged_files)} staged Python file(s)")
        
        # Stage 1: Code Parsing
        extractions = run_stage1()
        
        if not extractions:
            console.print("[yellow]No files to analyze[/yellow]")
            return 0
        
        # Stage 2: Multi-Agent Analysis
        consensus_results = run_stage2(extractions)
        
        # Stage 3: Severity Debate
        debate_results = run_stage3(consensus_results)
        
        # Stage 4: Verification & Attack Trees
        verified_results = run_stage4(debate_results, consensus_results)
        
        # Stage 5: Terminal Report
        exit_code = run_stage5(verified_results)
        
        return exit_code
        
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Audit interrupted by user[/yellow]")
        return 2
        
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        import traceback
        console.print("[dim]" + traceback.format_exc() + "[/dim]")
        return 2


if __name__ == "__main__":
    exit_code = run_security_audit()
    sys.exit(exit_code)
