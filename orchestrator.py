"""
Main Orchestrator
Runs all 5 stages of the security audit pipeline.
"""

import os
import sys
from typing import Optional, Dict

from rich.console import Console

from tools.git_diff_extractor import get_staged_files, is_git_repository
from tools.ignore_filter import IgnoreFilter
from agents.code_parser import run_stage1
from agents.security_agents import run_stage2
from agents.debate_room import run_stage3
from agents.verifier import run_stage4
from agents.terminal_reporter import run_stage5
from parsers import ParserFactory

console = Console()


def run_security_audit(config: Optional[Dict] = None) -> int:
    """
    Main orchestrator - runs all 5 stages.

    Args:
        config: Configuration dict with options:
            - json_output: Output as JSON
            - summary_only: Show summary only
            - fail_on_critical: Exit 1 on CRITICAL (default)
            - fail_on_high: Exit 1 on HIGH or CRITICAL
            - strict_mode: Exit 1 on any vulnerability
            - warn_only: Never exit 1
            - baseline_mode: Create/update baseline
            - baseline_file: Path to baseline file
            - quick_mode: Skip stages 3-4
            - config_file: Path to config file
            - ignore_file: Path to ignore file

    Returns:
        Exit code (0=clean, 1=vulns found, 2=error)
    """
    if config is None:
        config = {
            'json_output': False,
            'summary_only': False,
            'fail_on_critical': True,
            'fail_on_high': False,
            'strict_mode': False,
            'warn_only': False,
            'baseline_mode': False,
            'baseline_file': '.secaudit-baseline.json',
            'quick_mode': False,
            'config_file': '.secaudit.yaml',
            'ignore_file': '.secaudit-ignore',
        }
    try:
        os.makedirs('cache', exist_ok=True)
        if not config.get('json_output'):
            console.print("\n[bold cyan]Security Audit Pipeline[/bold cyan]")
            console.print("[dim]Multi-agent security analysis for Python code[/dim]\n")

        # Check if in git repository
        if not is_git_repository():
            if not config.get('json_output'):
                console.print("[red]Error: Not a git repository[/red]")
                console.print("This tool must be run inside a git repository")
            return 2

        # Check for staged files
        supported_extensions = ParserFactory.get_supported_extensions()
        staged_files = get_staged_files(supported_extensions)

        if not staged_files:
            if not config.get('json_output'):
                console.print("[yellow]No supported files staged[/yellow]")
                console.print(f"Supported extensions: {', '.join(supported_extensions)}")
                console.print("Stage some files with: git add <file>")
            return 0

        if not config.get('json_output'):
            console.print(f"[green]✓[/green] Found {len(staged_files)} staged file(s)")

        # Stage 1: Code Parsing (with file filters)
        extractions = run_stage1(config)

        if not extractions:
            if not config.get('json_output'):
                console.print("[yellow]No files to analyze[/yellow]")
            return 0

        # Stage 2: Multi-Agent Analysis
        consensus_results = run_stage2(extractions)

        # Stage 3: Severity Debate (skip if quick mode)
        if config.get('quick_mode'):
            # Convert consensus_results to debate_results format for stage 4
            all_vulns = []
            for result in consensus_results:
                all_vulns.extend(result.get('vulnerabilities', []))

            debate_results = {
                'skipped': False,
                'total_debated': len(all_vulns),
                'vulnerabilities': all_vulns
            }
        else:
            debate_results = run_stage3(consensus_results)

        # Stage 4: Verification & Attack Trees (skip if quick mode)
        if config.get('quick_mode'):
            # In quick mode, convert consensus directly to verified format
            verified_results = []
            for result in consensus_results:
                if result.get('vulnerabilities'):
                    verified_results.append({
                        'filepath': result['filepath'],
                        'vulnerabilities': result['vulnerabilities']
                    })
        else:
            verified_results = run_stage4(debate_results, consensus_results)

        # Apply ignore filter
        ignore_filter = IgnoreFilter(config.get('ignore_file', '.secaudit-ignore'))
        verified_results = ignore_filter.filter_vulnerabilities(verified_results)

        # Apply baseline filter if enabled
        if config.get('baseline_mode'):
            from tools.baseline_manager import BaselineManager
            baseline = BaselineManager(config.get('baseline_file', '.secaudit-baseline.json'))
            verified_results = baseline.filter_new_vulnerabilities(verified_results)

        # Stage 5: Terminal Report (with config for exit codes and output format)
        exit_code = run_stage5(verified_results, config)

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
