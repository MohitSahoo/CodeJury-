"""
Test config manager functionality.
"""

import os
import tempfile
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.config_manager import ConfigManager


def test_config_manager():
    """Test config manager with sample patterns."""
    # Create temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.secaudit.yaml', delete=False) as f:
        f.write("""# Test config
exclude:
  - 'test_*.py'
  - '*_test.py'
  - 'tests/**'
  - 'migrations/**'
  - '.venv/**'

min_confidence: MEDIUM
max_line_length: 500
""")
        config_file = f.name

    try:
        # Test loading
        config = ConfigManager(config_file)
        assert config.config is not None, "Config should be loaded"
        print("✓ Config loaded successfully")

        # Test exclude patterns
        test_cases = [
            ('src/auth.py', False),  # Should NOT be excluded
            ('test_auth.py', True),  # Should be excluded (test_*.py)
            ('auth_test.py', True),  # Should be excluded (*_test.py)
            ('tests/test_views.py', True),  # Should be excluded (tests/**)
            ('migrations/0001_initial.py', True),  # Should be excluded (migrations/**)
            ('.venv/lib/python3.9/site.py', True),  # Should be excluded (.venv/**)
            ('app/views.py', False),  # Should NOT be excluded
        ]

        for filepath, should_exclude in test_cases:
            result = config.should_exclude_file(filepath)
            assert result == should_exclude, f"Expected {filepath} to be {'excluded' if should_exclude else 'included'}, got {'excluded' if result else 'included'}"
            status = 'EXCLUDED' if result else 'INCLUDED'
            print(f"✓ {filepath}: {status}")

        # Test min confidence
        assert config.get_min_confidence() == 'MEDIUM', "Min confidence should be MEDIUM"
        print("✓ Min confidence setting works")

        # Test max line length
        assert config.get_max_line_length() == 500, "Max line length should be 500"
        print("✓ Max line length setting works")

        print("\n✅ All config manager tests passed!")

    finally:
        # Clean up
        os.unlink(config_file)


def test_default_config():
    """Test default config when file doesn't exist."""
    config = ConfigManager('nonexistent.yaml')

    # Should have default exclude patterns
    assert len(config.config['exclude']) > 0, "Should have default exclude patterns"
    print("✓ Default config loaded when file doesn't exist")

    # Test that test files are excluded by default
    assert config.should_exclude_file('test_something.py'), "test_*.py should be excluded by default"
    assert config.should_exclude_file('tests/test_views.py'), "tests/** should be excluded by default"
    print("✓ Default exclusions work")

    print("\n✅ Default config tests passed!")


if __name__ == "__main__":
    test_config_manager()
    test_default_config()
