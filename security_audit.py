#!/usr/bin/env python3
"""
Security Audit Pipeline - CLI Entry Point
Multi-agent security analysis for Python code via pre-commit hook.
"""

import sys
import os
import argparse

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestrator import run_security_audit


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Multi-agent security audit for Python code",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage (pre-commit hook)
  python security_audit.py

  # Create baseline (first run on existing codebase)
  python security_audit.py --baseline

  # JSON output for CI/CD
  python security_audit.py --json --fail-on-high

  # Strict mode (fail on any vulnerability)
  python security_audit.py --strict

  # Warn only (never block commits)
  python security_audit.py --warn-only
        """
    )

    # Output modes
    output_group = parser.add_argument_group('Output Options')
    output_group.add_argument(
        '--json',
        action='store_true',
        help='Output results as JSON (for CI/CD integration)'
    )
    output_group.add_argument(
        '--summary',
        action='store_true',
        help='Show summary only (fast feedback)'
    )
    output_group.add_argument(
        '--sarif',
        action='store_true',
        help='Output results in SARIF format (standard for industry security tools)'
    )

    # Exit code modes
    exit_group = parser.add_argument_group('Exit Code Options')
    exit_mode = exit_group.add_mutually_exclusive_group()
    exit_mode.add_argument(
        '--fail-on-critical',
        action='store_true',
        help='Exit 1 only on CRITICAL vulnerabilities (default)'
    )
    exit_mode.add_argument(
        '--fail-on-high',
        action='store_true',
        help='Exit 1 on HIGH or CRITICAL vulnerabilities'
    )
    exit_mode.add_argument(
        '--strict',
        action='store_true',
        help='Exit 1 on any vulnerability (CRITICAL, HIGH, MEDIUM, LOW)'
    )
    exit_mode.add_argument(
        '--warn-only',
        action='store_true',
        help='Never exit 1 (always allow commits, just warn)'
    )

    # Baseline mode
    baseline_group = parser.add_argument_group('Baseline Options')
    baseline_group.add_argument(
        '--baseline',
        action='store_true',
        help='Create or update baseline (only show new vulnerabilities on subsequent runs)'
    )
    baseline_group.add_argument(
        '--baseline-file',
        default='.secaudit-baseline.json',
        help='Path to baseline file (default: .secaudit-baseline.json)'
    )

    # Performance options
    perf_group = parser.add_argument_group('Performance Options')
    perf_group.add_argument(
        '--quick',
        action='store_true',
        help='Skip debate and verification stages (faster but less accurate)'
    )

    # Config file
    parser.add_argument(
        '--config',
        default='.secaudit.yaml',
        help='Path to config file (default: .secaudit.yaml)'
    )

    # Ignore file
    parser.add_argument(
        '--ignore-file',
        default='.secaudit-ignore',
        help='Path to ignore file (default: .secaudit-ignore)'
    )

    return parser.parse_args()


def main():
    """Main entry point for security audit."""
    try:
        args = parse_args()

        # Build config dict from args
        config = {
            'json_output': args.json,
            'summary_only': args.summary,
            'sarif_output': args.sarif,
            'fail_on_critical': args.fail_on_critical or (not args.fail_on_high and not args.strict and not args.warn_only),
            'fail_on_high': args.fail_on_high,
            'strict_mode': args.strict,
            'warn_only': args.warn_only,
            'baseline_mode': args.baseline,
            'baseline_file': args.baseline_file,
            'quick_mode': args.quick,
            'config_file': args.config,
            'ignore_file': args.ignore_file,
        }

        exit_code = run_security_audit(config)
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nAudit interrupted by user")
        sys.exit(2)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()
