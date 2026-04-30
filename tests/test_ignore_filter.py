"""
Test ignore filter functionality.
"""

import os
import tempfile
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.ignore_filter import IgnoreFilter


def test_ignore_filter():
    """Test ignore filter with sample rules."""
    # Create temporary ignore file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.secaudit-ignore', delete=False) as f:
        f.write("""# Test ignore file
auth.py:47:SQL_INJECTION  # test code
views.py:23:XSS  # sanitized elsewhere
utils.py:*:COMMAND_INJECTION  # ignore all
""")
        ignore_file = f.name

    try:
        # Test loading
        filter = IgnoreFilter(ignore_file)
        assert len(filter.ignore_rules) == 3, f"Expected 3 rules, got {len(filter.ignore_rules)}"
        print("✓ Loaded 3 ignore rules")

        # Test exact match
        assert filter.should_ignore('auth.py', '47', 'SQL_INJECTION'), "Should ignore auth.py:47:SQL_INJECTION"
        print("✓ Exact match works")

        # Test non-match
        assert not filter.should_ignore('auth.py', '48', 'SQL_INJECTION'), "Should not ignore auth.py:48"
        print("✓ Non-match works")

        # Test wildcard line number
        assert filter.should_ignore('utils.py', '100', 'COMMAND_INJECTION'), "Should ignore utils.py:*:COMMAND_INJECTION"
        print("✓ Wildcard line number works")

        # Test filtering vulnerabilities
        test_results = [
            {
                'filepath': 'auth.py',
                'vulnerabilities': [
                    {'type': 'SQL_INJECTION', 'location': '47'},
                    {'type': 'XSS', 'location': '50'},
                ]
            },
            {
                'filepath': 'views.py',
                'vulnerabilities': [
                    {'type': 'XSS', 'location': '23'},
                ]
            }
        ]

        filtered = filter.filter_vulnerabilities(test_results)

        # Should have 1 result (auth.py with 1 vuln)
        assert len(filtered) == 1, f"Expected 1 result, got {len(filtered)}"
        assert len(filtered[0]['vulnerabilities']) == 1, "Expected 1 vulnerability in auth.py"
        assert filtered[0]['vulnerabilities'][0]['type'] == 'XSS', "Expected XSS vulnerability"
        print("✓ Vulnerability filtering works")

        print("\n✅ All ignore filter tests passed!")

    finally:
        # Clean up
        os.unlink(ignore_file)


if __name__ == "__main__":
    test_ignore_filter()
