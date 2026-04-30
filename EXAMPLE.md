# Security Audit Pipeline - Examples

## Quick Start

```bash
# Stage your Python files
git add app.py utils.py

# Run security audit
python3 security_audit.py
```

## Example: Detecting SQL Injection

**Vulnerable Code:**
```python
def login(username, password):
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    cursor.execute(query)
    return cursor.fetchone()
```

**Detection Output:**
```
╭─────────────────────────────── Vulnerability ────────────────────────────────╮
│ SQL_INJECTION                                                                │
│ Location: app.py:12                                                          │
│ Severity: HIGH (Confidence: HIGH)                                            │
│ CWE: CWE-89                                                                  │
│                                                                              │
│ SQL injection vulnerability allowing attackers to bypass authentication      │
│                                                                              │
│ Mitigation:                                                                  │
│ Use parameterized queries instead of string formatting                       │
╰──────────────────────────────────────────────────────────────────────────────╯
```

**Fixed Code:**
```python
def login(username, password):
    query = "SELECT * FROM users WHERE username=? AND password=?"
    cursor.execute(query, (username, password))
    return cursor.fetchone()
```

## Example: Detecting Command Injection

**Vulnerable Code:**
```python
def process_file(filename):
    os.system(f"cat {filename}")
```

**Detection Output:**
```
╭─────────────────────────────── Vulnerability ────────────────────────────────╮
│ COMMAND_INJECTION                                                            │
│ Location: utils.py:45                                                        │
│ Severity: CRITICAL (Confidence: HIGH)                                        │
│ CWE: CWE-78                                                                  │
│                                                                              │
│ Command injection allowing arbitrary system command execution                │
│                                                                              │
│ Mitigation:                                                                  │
│ Never use shell=True. Use subprocess with argument lists                     │
╰──────────────────────────────────────────────────────────────────────────────╯
```

**Fixed Code:**
```python
def process_file(filename):
    subprocess.run(['cat', filename], check=True)
```

## Example: Secrets Detection

**Vulnerable Code:**
```python
api_key = "sk_live_51H8xYzABC123456789"
aws_key = "AKIAIOSFODNN7EXAMPLE"
```

**Detection Output:**
```
⚠️  SECRETS DETECTED - DO NOT COMMIT
================================================================================
  STRIPE_KEY
  Location: config.py:5
  Preview: sk_live_...789

  AWS_ACCESS_KEY
  Location: config.py:6
  Preview: AKIA...

Recommendations:
  1. Remove secrets from code
  2. Use environment variables
  3. Add .env to .gitignore
  4. Rotate exposed credentials
```

**Fixed Code:**
```python
import os
api_key = os.getenv('STRIPE_API_KEY')
aws_key = os.getenv('AWS_ACCESS_KEY')
```

## Configuration

Create `.secaudit.yaml`:

```yaml
# Exclude patterns
exclude:
  - '*_test.py'
  - 'tests/**'
  - 'migrations/**'
  - 'venv/**'

# Minimum confidence to report
min_confidence: MEDIUM
```

## Attack Trees

The pipeline generates attack trees showing exploitation paths:

```
🎯 Compromise system via code execution
├── SQL_INJECTION (EASY difficulty, 5-15 minutes)
│   ├── 1. Identify SQL injection point
│   ├── 2. Craft malicious payload
│   ├── 3. Bypass authentication
│   └── Impact: Full database access
└── COMMAND_INJECTION (MEDIUM difficulty, 15-30 minutes)
    ├── 1. Identify command injection
    ├── 2. Inject shell metacharacters
    ├── 3. Execute arbitrary commands
    └── Impact: Remote code execution
```

## API Resilience

The pipeline handles API failures gracefully:

```
Agent A (Static Analysis - Gemini)...
  ⚠ gemini-2.0-flash rate limited, trying fallback...
  ✓ Found 3 vulnerabilities (using gemini-1.5-flash)

⚠ Running with 2/3 agents (degraded mode)
```

## Integration

### Pre-commit Hook

```bash
# .git/hooks/pre-commit
#!/bin/bash
python3 security_audit.py
if [ $? -ne 0 ]; then
    echo "Security audit failed - fix vulnerabilities before committing"
    exit 1
fi
```

### GitHub Actions

```yaml
name: Security Audit
on: [push, pull_request]
jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Security Audit
        run: python3 security_audit.py
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
```
