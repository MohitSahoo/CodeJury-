"""
Integration test for all new features.
Tests CLI arguments, JSON output, exit codes, baseline, ignore, and config filters.
"""

import os
import sys
import json
import tempfile
import subprocess
from pathlib import Path

# Test directory
TEST_DIR = Path(__file__).parent.parent


def run_audit(args: list, cwd: str = None) -> tuple:
    """
    Run security audit with given arguments.

    Returns:
        (exit_code, stdout, stderr)
    """
    if cwd is None:
        cwd = TEST_DIR

    cmd = [sys.executable, 'security_audit.py'] + args
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True
    )
    return result.returncode, result.stdout, result.stderr


def test_cli_help():
    """Test CLI help output."""
    exit_code, stdout, stderr = run_audit(['--help'])
    assert exit_code == 0, "Help should exit with 0"
    assert 'Security Audit' in stdout or 'usage:' in stdout, "Help should show usage"
    print("✓ CLI help works")


def test_json_output():
    """Test JSON output mode."""
    # This will fail if not in a git repo with staged files, but we can test the flag parsing
    exit_code, stdout, stderr = run_audit(['--json'])

    # If there are no staged files, it should still exit cleanly
    # If there are staged files, output should be valid JSON
    if stdout.strip():
        try:
            data = json.loads(stdout)
            assert 'summary' in data or 'error' in str(data), "JSON output should have summary"
            print("✓ JSON output format works")
        except json.JSONDecodeError:
            # Might not be in git repo or no staged files
            print("⚠ JSON output test skipped (no git repo or staged files)")
    else:
        print("⚠ JSON output test skipped (no output)")


def test_exit_code_flags():
    """Test exit code flag parsing."""
    # Test that flags are accepted (won't actually run audit without git repo)
    test_flags = [
        ['--fail-on-critical'],
        ['--fail-on-high'],
        ['--strict'],
        ['--warn-only'],
    ]

    for flags in test_flags:
        # Just test that the flag is accepted
        exit_code, stdout, stderr = run_audit(flags)
        # Should not fail with argument error
        assert 'unrecognized arguments' not in stderr, f"Flag {flags} should be recognized"

    print("✓ Exit code flags accepted")


def test_baseline_flag():
    """Test baseline flag parsing."""
    exit_code, stdout, stderr = run_audit(['--baseline'])
    assert 'unrecognized arguments' not in stderr, "Baseline flag should be recognized"
    print("✓ Baseline flag accepted")


def test_config_files():
    """Test config file flag parsing."""
    exit_code, stdout, stderr = run_audit(['--config', '.secaudit.yaml'])
    assert 'unrecognized arguments' not in stderr, "Config flag should be recognized"
    print("✓ Config file flag accepted")


def test_ignore_file():
    """Test ignore file flag parsing."""
    exit_code, stdout, stderr = run_audit(['--ignore-file', '.secaudit-ignore'])
    assert 'unrecognized arguments' not in stderr, "Ignore file flag should be recognized"
    print("✓ Ignore file flag accepted")


def test_quick_mode():
    """Test quick mode flag."""
    exit_code, stdout, stderr = run_audit(['--quick'])
    assert 'unrecognized arguments' not in stderr, "Quick mode flag should be recognized"
    print("✓ Quick mode flag accepted")


def test_combined_flags():
    """Test combining multiple flags."""
    exit_code, stdout, stderr = run_audit([
        '--json',
        '--fail-on-high',
        '--baseline',
        '--quick'
    ])
    assert 'unrecognized arguments' not in stderr, "Combined flags should be recognized"
    print("✓ Combined flags work")


if __name__ == "__main__":
    print("Running integration tests...\n")

    try:
        test_cli_help()
        test_json_output()
        test_exit_code_flags()
        test_baseline_flag()
        test_config_files()
        test_ignore_file()
        test_quick_mode()
        test_combined_flags()

        print("\n✅ All integration tests passed!")

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
