"""
Config File Parser
Load configuration from .secaudit.yaml for file filters and other settings.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List
import fnmatch


class ConfigManager:
    """Manage configuration from .secaudit.yaml file."""

    def __init__(self, config_file: str = '.secaudit.yaml'):
        """
        Initialize config manager.

        Args:
            config_file: Path to config file
        """
        self.config_file = Path(config_file)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_file.exists():
            return self._default_config()

        try:
            with open(self.config_file, 'r') as f:
                config = yaml.safe_load(f) or {}
                return {**self._default_config(), **config}
        except Exception as e:
            print(f"Warning: Failed to load config file: {e}")
            return self._default_config()

    def _default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            'exclude': [
                '*_test.py',
                'tests/**',
                'migrations/**',
                '__pycache__/**',
                '.venv/**',
                'venv/**',
                'env/**',
                '.tox/**',
                'build/**',
                'dist/**',
                '*.egg-info/**',
            ],
            'include': [],  # If specified, only these patterns are included
            'min_confidence': 'LOW',  # Minimum confidence to report
            'max_line_length': 500,  # Skip very long lines (likely generated code)
        }

    def should_exclude_file(self, filepath: str) -> bool:
        """
        Check if file should be excluded based on patterns.

        Args:
            filepath: File path to check

        Returns:
            True if file should be excluded
        """
        filepath_normalized = Path(filepath).as_posix()

        # Check include patterns first (if specified)
        include_patterns = self.config.get('include', [])
        if include_patterns:
            included = any(
                fnmatch.fnmatch(filepath_normalized, pattern)
                for pattern in include_patterns
            )
            if not included:
                return True

        # Check exclude patterns
        exclude_patterns = self.config.get('exclude', [])
        for pattern in exclude_patterns:
            if fnmatch.fnmatch(filepath_normalized, pattern):
                return True

            # Also check just the filename
            filename = Path(filepath).name
            if fnmatch.fnmatch(filename, pattern):
                return True

        return False

    def get_min_confidence(self) -> str:
        """Get minimum confidence level to report."""
        return self.config.get('min_confidence', 'LOW')

    def get_max_line_length(self) -> int:
        """Get maximum line length before skipping."""
        return self.config.get('max_line_length', 500)


def create_config_template(config_file: str = '.secaudit.yaml') -> None:
    """
    Create template config file with examples.

    Args:
        config_file: Path to config file
    """
    template = """# Security Audit Configuration
# Exclude patterns (glob syntax)
exclude:
  # Test files
  - 'test_*.py'
  - '*_test.py'
  - 'tests/**'

  # Migrations and generated code
  - 'migrations/**'
  - '**/migrations/**'
  - '__generated__/**'

  # Virtual environments
  - '.venv/**'
  - 'venv/**'
  - 'env/**'

  # Build artifacts
  - '__pycache__/**'
  - '.tox/**'
  - 'build/**'
  - 'dist/**'
  - '*.egg-info/**'

# Include patterns (optional - if specified, only these are scanned)
# include:
#   - 'src/**'
#   - 'app/**'

# Minimum confidence level to report (LOW, MEDIUM, HIGH)
min_confidence: LOW

# Maximum line length before skipping (likely generated code)
max_line_length: 500
"""

    path = Path(config_file)
    if not path.exists():
        with open(path, 'w') as f:
            f.write(template)
        print(f"Created config file template: {config_file}")


if __name__ == "__main__":
    # Test config manager
    create_config_template()

    # Test loading
    config = ConfigManager('.secaudit.yaml')
    print(f"Loaded config: {config.config}")

    # Test exclusion
    test_files = [
        'src/auth.py',
        'test_auth.py',
        'tests/test_auth.py',
        'migrations/0001_initial.py',
        'venv/lib/python3.9/site.py',
    ]

    for filepath in test_files:
        excluded = config.should_exclude_file(filepath)
        print(f"{filepath}: {'EXCLUDED' if excluded else 'INCLUDED'}")
