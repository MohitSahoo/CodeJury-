"""
Secrets detection to prevent API keys and credentials from being committed.
Scans code for common secret patterns before sending to AI agents.
"""

import re
from typing import List, Dict

# Common secret patterns
SECRET_PATTERNS = {
    'generic_api_key': r'(?i)(api[_-]?key|apikey|api[_-]?secret)["\']?\s*[:=]\s*["\']([A-Za-z0-9_\-]{20,})["\']',
    'aws_access_key': r'AKIA[0-9A-Z]{16}',
    'aws_secret_key': r'(?i)aws[_-]?secret[_-]?access[_-]?key["\']?\s*[:=]\s*["\']([A-Za-z0-9/+=]{40})["\']',
    'github_token': r'gh[pousr]_[A-Za-z0-9_]{36,}',
    'slack_token': r'xox[baprs]-[0-9]{10,13}-[0-9]{10,13}-[A-Za-z0-9]{24,}',
    'private_key': r'-----BEGIN\s+(?:RSA|DSA|EC|OPENSSH)\s+PRIVATE\s+KEY-----',
    'google_api_key': r'AIza[0-9A-Za-z\-_]{35}',
    'stripe_key': r'(?:sk|pk)_(test|live)_[0-9a-zA-Z]{24,}',
    'jwt_token': r'eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}',
    'password_in_url': r'(?i)[a-z]{3,10}://[^/\s:@]{3,20}:[^/\s:@]{3,20}@.{1,100}',
    'generic_secret': r'(?i)(secret|password|passwd|pwd)["\']?\s*[:=]\s*["\']([^"\'\s]{8,})["\']',
}

# Patterns to ignore (common false positives)
IGNORE_PATTERNS = [
    r'example\.com',
    r'localhost',
    r'127\.0\.0\.1',
    r'0\.0\.0\.0',
    r'test[_-]?key',
    r'dummy[_-]?key',
    r'fake[_-]?key',
    r'your[_-]?key',
    r'<.*>',  # Placeholders
    r'\$\{.*\}',  # Environment variables
    r'%\(.*\)',  # Python string formatting
]


def scan_for_secrets(code: str, filename: str = "") -> List[Dict[str, str]]:
    """
    Scan code for potential secrets.

    Args:
        code: Source code to scan
        filename: Optional filename for context

    Returns:
        List of detected secrets with type, line number, and preview
    """
    secrets = []
    lines = code.split('\n')

    for line_num, line in enumerate(lines, 1):
        # Skip comments (basic detection)
        if line.strip().startswith('#') or line.strip().startswith('//'):
            continue

        # Check if line should be ignored
        if any(re.search(pattern, line, re.IGNORECASE) for pattern in IGNORE_PATTERNS):
            continue

        # Check each secret pattern
        for secret_type, pattern in SECRET_PATTERNS.items():
            matches = re.finditer(pattern, line)
            for match in matches:
                # Get the matched secret (mask it for display)
                secret_value = match.group(0)
                if len(secret_value) > 20:
                    masked = secret_value[:8] + '...' + secret_value[-4:]
                else:
                    masked = secret_value[:4] + '...'

                secrets.append({
                    'type': secret_type,
                    'line': line_num,
                    'file': filename,
                    'preview': masked,
                    'full_line': line.strip()[:80]  # First 80 chars
                })

    return secrets


def check_env_file_staged() -> bool:
    """
    Check if .env file is staged for commit.
    Returns True if .env is staged.
    """
    import subprocess
    try:
        result = subprocess.run(
            ['git', 'diff', '--cached', '--name-only'],
            capture_output=True,
            text=True,
            check=True
        )
        staged_files = result.stdout.strip().split('\n')
        return any('.env' in f for f in staged_files)
    except:
        return False


def format_secrets_warning(secrets: List[Dict[str, str]]) -> str:
    """
    Format detected secrets into a user-friendly warning message.
    """
    if not secrets:
        return ""

    warning = "\n" + "="*80 + "\n"
    warning += "⚠️  SECRETS DETECTED - DO NOT COMMIT\n"
    warning += "="*80 + "\n\n"

    for secret in secrets:
        warning += f"  {secret['type'].upper()}\n"
        warning += f"  Location: {secret['file']}:{secret['line']}\n"
        warning += f"  Preview: {secret['preview']}\n"
        warning += f"  Line: {secret['full_line']}\n\n"

    warning += "Recommendations:\n"
    warning += "  1. Remove secrets from code\n"
    warning += "  2. Use environment variables instead\n"
    warning += "  3. Add .env to .gitignore\n"
    warning += "  4. Rotate any exposed credentials\n"
    warning += "="*80 + "\n"

    return warning


if __name__ == "__main__":
    # Test with sample code
    test_code = """
import os

# Good - using environment variable
api_key = os.getenv('API_KEY')

# Bad - hardcoded secret
api_key = "sk_live_51H8xYzABC123456789"
aws_key = "AKIAIOSFODNN7EXAMPLE"
password = "super_secret_password_123"

# Should be ignored
example_key = "your_api_key_here"
test_key = "test_key_12345"
"""

    secrets = scan_for_secrets(test_code, "test.py")
    print(format_secrets_warning(secrets))
    print(f"\nFound {len(secrets)} potential secret(s)")
