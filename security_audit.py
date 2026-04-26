#!/usr/bin/env python3
"""
Security Audit Pipeline - CLI Entry Point
Multi-agent security analysis for Python code via pre-commit hook.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestrator import run_security_audit


def main():
    """Main entry point for security audit."""
    try:
        exit_code = run_security_audit()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nAudit interrupted by user")
        sys.exit(2)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()
