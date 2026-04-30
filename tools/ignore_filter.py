"""
Ignore File Parser
Filters out false positives marked in .secaudit-ignore file.
"""

from pathlib import Path
from typing import List, Dict, Any, Set, Tuple


class IgnoreFilter:
    """Parse and apply ignore rules from .secaudit-ignore file."""

    def __init__(self, ignore_file: str = '.secaudit-ignore'):
        """
        Initialize ignore filter.

        Args:
            ignore_file: Path to ignore file
        """
        self.ignore_file = Path(ignore_file)
        self.ignore_rules: Set[Tuple[str, str, str]] = set()
        self._load_rules()

    def _load_rules(self) -> None:
        """Load ignore rules from file."""
        if not self.ignore_file.exists():
            return

        try:
            with open(self.ignore_file, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()

                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue

                    # Remove inline comments
                    if '#' in line:
                        line = line.split('#')[0].strip()

                    # Parse rule: filepath:line:VULN_TYPE
                    parts = line.split(':')
                    if len(parts) < 3:
                        print(f"Warning: Invalid ignore rule at line {line_num}: {line}")
                        continue

                    filepath = parts[0].strip()
                    line_no = parts[1].strip()
                    vuln_type = ':'.join(parts[2:]).strip()  # Handle vuln types with colons

                    self.ignore_rules.add((filepath, line_no, vuln_type))

        except Exception as e:
            print(f"Warning: Failed to load ignore file: {e}")

    def should_ignore(self, filepath: str, location: str, vuln_type: str) -> bool:
        """
        Check if vulnerability should be ignored.

        Args:
            filepath: File path of vulnerability
            location: Location string (e.g., "file.py:42" or "42")
            vuln_type: Vulnerability type

        Returns:
            True if should be ignored
        """
        # Extract line number from location
        if ':' in location:
            line_no = location.split(':')[-1]
        else:
            line_no = location

        # Normalize filepath (handle relative paths)
        filepath_normalized = Path(filepath).as_posix()

        # Check exact match
        if (filepath_normalized, line_no, vuln_type) in self.ignore_rules:
            return True

        # Check with just filename (not full path)
        filename = Path(filepath).name
        if (filename, line_no, vuln_type) in self.ignore_rules:
            return True

        # Check wildcard line number (filepath:*:VULN_TYPE)
        if (filepath_normalized, '*', vuln_type) in self.ignore_rules:
            return True

        if (filename, '*', vuln_type) in self.ignore_rules:
            return True

        return False

    def filter_vulnerabilities(self, verified_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter out ignored vulnerabilities from results.

        Args:
            verified_results: List of verified results from Stage 4

        Returns:
            Filtered results with ignored vulnerabilities removed
        """
        if not self.ignore_rules:
            return verified_results

        filtered_results = []
        ignored_count = 0

        for result in verified_results:
            filepath = result.get('filepath', '')
            vulns = result.get('vulnerabilities', [])

            filtered_vulns = []
            for vuln in vulns:
                location = vuln.get('location', '')
                vuln_type = vuln.get('type', '')

                if self.should_ignore(filepath, location, vuln_type):
                    ignored_count += 1
                    continue

                filtered_vulns.append(vuln)

            # Only include result if it has vulnerabilities after filtering
            if filtered_vulns:
                result_copy = result.copy()
                result_copy['vulnerabilities'] = filtered_vulns
                filtered_results.append(result_copy)

        if ignored_count > 0:
            print(f"Filtered out {ignored_count} ignored vulnerability(ies)")

        return filtered_results


def create_ignore_template(ignore_file: str = '.secaudit-ignore') -> None:
    """
    Create template ignore file with examples.

    Args:
        ignore_file: Path to ignore file
    """
    template = """# Security Audit Ignore File
# Format: filepath:line:VULN_TYPE  # optional comment
#
# Examples:
#   auth.py:47:SQL_INJECTION  # test code, safe
#   views.py:23:XSS  # input is sanitized elsewhere
#   utils.py:*:COMMAND_INJECTION  # ignore all in this file
#
# Supported wildcards:
#   - Use * for line number to ignore all occurrences in a file
#   - Use just filename (not full path) for portability
#
# Add your ignore rules below:

"""

    path = Path(ignore_file)
    if not path.exists():
        with open(path, 'w') as f:
            f.write(template)
        print(f"Created ignore file template: {ignore_file}")


if __name__ == "__main__":
    # Test ignore filter
    create_ignore_template()

    # Test parsing
    filter = IgnoreFilter('.secaudit-ignore')
    print(f"Loaded {len(filter.ignore_rules)} ignore rules")

    # Test filtering
    test_results = [
        {
            'filepath': 'auth.py',
            'vulnerabilities': [
                {'type': 'SQL_INJECTION', 'location': 'auth.py:47'},
                {'type': 'XSS', 'location': 'auth.py:50'},
            ]
        }
    ]

    filtered = filter.filter_vulnerabilities(test_results)
    print(f"Filtered results: {filtered}")
