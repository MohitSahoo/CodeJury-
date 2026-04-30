"""
Baseline Manager
Track vulnerabilities over time and only report new ones.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Set
from datetime import datetime


class BaselineManager:
    """Manage baseline of known vulnerabilities."""

    def __init__(self, baseline_file: str = '.secaudit-baseline.json'):
        """
        Initialize baseline manager.

        Args:
            baseline_file: Path to baseline file
        """
        self.baseline_file = Path(baseline_file)
        self.baseline: Dict[str, Any] = self._load_baseline()

    def _load_baseline(self) -> Dict[str, Any]:
        """Load baseline from file."""
        if not self.baseline_file.exists():
            return {
                'created_at': None,
                'updated_at': None,
                'vulnerabilities': []
            }

        try:
            with open(self.baseline_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load baseline file: {e}")
            return {
                'created_at': None,
                'updated_at': None,
                'vulnerabilities': []
            }

    def _save_baseline(self, vulnerabilities: List[Dict[str, Any]]) -> None:
        """
        Save baseline to file.

        Args:
            vulnerabilities: List of vulnerabilities to save
        """
        now = datetime.now().isoformat()

        baseline_data = {
            'created_at': self.baseline.get('created_at') or now,
            'updated_at': now,
            'vulnerabilities': vulnerabilities
        }

        try:
            with open(self.baseline_file, 'w') as f:
                json.dump(baseline_data, f, indent=2)
            print(f"Baseline saved to {self.baseline_file}")
        except Exception as e:
            print(f"Warning: Failed to save baseline: {e}")

    def _vulnerability_key(self, vuln: Dict[str, Any], filepath: str) -> str:
        """
        Generate unique key for vulnerability.

        Args:
            vuln: Vulnerability dict
            filepath: File path

        Returns:
            Unique key string
        """
        vuln_type = vuln.get('type', '')
        location = vuln.get('location', '')
        evidence = vuln.get('evidence', '')[:100]  # First 100 chars

        return f"{filepath}:{location}:{vuln_type}:{evidence}"

    def filter_new_vulnerabilities(self, verified_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter results to only show new vulnerabilities not in baseline.

        Args:
            verified_results: List of verified results from Stage 4

        Returns:
            Filtered results with only new vulnerabilities
        """
        # Build set of baseline vulnerability keys
        baseline_keys: Set[str] = set()
        for baseline_vuln in self.baseline.get('vulnerabilities', []):
            filepath = baseline_vuln.get('filepath', '')
            key = self._vulnerability_key(baseline_vuln, filepath)
            baseline_keys.add(key)

        # Filter to only new vulnerabilities
        filtered_results = []
        new_count = 0
        existing_count = 0

        all_current_vulns = []

        for result in verified_results:
            filepath = result.get('filepath', '')
            vulns = result.get('vulnerabilities', [])

            new_vulns = []
            for vuln in vulns:
                # Save all current vulnerabilities for baseline update
                vuln_with_filepath = vuln.copy()
                vuln_with_filepath['filepath'] = filepath
                all_current_vulns.append(vuln_with_filepath)

                # Check if this is a new vulnerability
                key = self._vulnerability_key(vuln, filepath)
                if key not in baseline_keys:
                    new_vulns.append(vuln)
                    new_count += 1
                else:
                    existing_count += 1

            # Only include result if it has new vulnerabilities
            if new_vulns:
                result_copy = result.copy()
                result_copy['vulnerabilities'] = new_vulns
                filtered_results.append(result_copy)

        # Update baseline with current vulnerabilities
        self._save_baseline(all_current_vulns)

        # Print summary
        if self.baseline.get('created_at'):
            print(f"Baseline mode: {new_count} new, {existing_count} existing (suppressed)")
        else:
            print(f"Baseline created with {len(all_current_vulns)} vulnerability(ies)")

        return filtered_results

    def clear_baseline(self) -> None:
        """Clear baseline file."""
        if self.baseline_file.exists():
            self.baseline_file.unlink()
            print(f"Baseline cleared: {self.baseline_file}")


if __name__ == "__main__":
    # Test baseline manager
    manager = BaselineManager('.secaudit-baseline.json')

    # Test with sample vulnerabilities
    test_results = [
        {
            'filepath': 'auth.py',
            'vulnerabilities': [
                {
                    'type': 'SQL_INJECTION',
                    'location': 'auth.py:47',
                    'evidence': 'query = f"SELECT * FROM users WHERE username=\'{username}\'"'
                },
                {
                    'type': 'XSS',
                    'location': 'auth.py:50',
                    'evidence': 'return f"<div>{user_input}</div>"'
                }
            ]
        }
    ]

    # First run - should show all
    print("First run:")
    filtered = manager.filter_new_vulnerabilities(test_results)
    print(f"New vulnerabilities: {len(filtered[0]['vulnerabilities']) if filtered else 0}")

    # Second run - should show none (all in baseline)
    print("\nSecond run:")
    manager2 = BaselineManager('.secaudit-baseline.json')
    filtered2 = manager2.filter_new_vulnerabilities(test_results)
    print(f"New vulnerabilities: {len(filtered2)}")

    # Clean up
    manager.clear_baseline()
