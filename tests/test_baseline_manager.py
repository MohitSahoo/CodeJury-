"""
Test baseline manager functionality.
"""

import os
import tempfile
import json
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.baseline_manager import BaselineManager


def test_baseline_manager():
    """Test baseline manager with sample vulnerabilities."""
    # Create temporary baseline file (secure)
    fd, baseline_file = tempfile.mkstemp(suffix='.secaudit-baseline.json')
    os.close(fd)  # Close file descriptor, we'll use the path

    try:
        # Test initial baseline creation
        manager = BaselineManager(baseline_file)

        test_results = [
            {
                'filepath': 'auth.py',
                'vulnerabilities': [
                    {
                        'type': 'SQL_INJECTION',
                        'location': 'auth.py:47',
                        'evidence': 'query = f"SELECT * FROM users WHERE username=\'{username}\'"',
                        'severity': 'CRITICAL'
                    },
                    {
                        'type': 'XSS',
                        'location': 'auth.py:50',
                        'evidence': 'return f"<div>{user_input}</div>"',
                        'severity': 'HIGH'
                    }
                ]
            }
        ]

        # First run - should show all vulnerabilities
        filtered = manager.filter_new_vulnerabilities(test_results)
        assert len(filtered) == 1, f"Expected 1 result, got {len(filtered)}"
        assert len(filtered[0]['vulnerabilities']) == 2, "Expected 2 vulnerabilities on first run"
        print("✓ First run shows all vulnerabilities")

        # Verify baseline file was created
        assert Path(baseline_file).exists(), "Baseline file should be created"
        print("✓ Baseline file created")

        # Second run with same vulnerabilities - should show none
        manager2 = BaselineManager(baseline_file)
        filtered2 = manager2.filter_new_vulnerabilities(test_results)
        assert len(filtered2) == 0, f"Expected 0 results on second run, got {len(filtered2)}"
        print("✓ Second run shows no vulnerabilities (all in baseline)")

        # Third run with new vulnerability - should show only new one
        test_results_with_new = [
            {
                'filepath': 'auth.py',
                'vulnerabilities': [
                    {
                        'type': 'SQL_INJECTION',
                        'location': 'auth.py:47',
                        'evidence': 'query = f"SELECT * FROM users WHERE username=\'{username}\'"',
                        'severity': 'CRITICAL'
                    },
                    {
                        'type': 'XSS',
                        'location': 'auth.py:50',
                        'evidence': 'return f"<div>{user_input}</div>"',
                        'severity': 'HIGH'
                    },
                    {
                        'type': 'COMMAND_INJECTION',
                        'location': 'auth.py:60',
                        'evidence': 'os.system(f"echo {user_input}")',
                        'severity': 'CRITICAL'
                    }
                ]
            }
        ]

        manager3 = BaselineManager(baseline_file)
        filtered3 = manager3.filter_new_vulnerabilities(test_results_with_new)
        assert len(filtered3) == 1, f"Expected 1 result, got {len(filtered3)}"
        assert len(filtered3[0]['vulnerabilities']) == 1, "Expected 1 new vulnerability"
        assert filtered3[0]['vulnerabilities'][0]['type'] == 'COMMAND_INJECTION', "Expected COMMAND_INJECTION"
        print("✓ Third run shows only new vulnerability")

        # Test baseline clearing
        manager3.clear_baseline()
        assert not Path(baseline_file).exists(), "Baseline file should be deleted"
        print("✓ Baseline clearing works")

        print("\n✅ All baseline manager tests passed!")

    finally:
        # Clean up
        if Path(baseline_file).exists():
            os.unlink(baseline_file)


if __name__ == "__main__":
    test_baseline_manager()
