# Usage Guide

Complete guide to using the Security Audit Pipeline.

## Table of Contents

1. [Basic Usage](#basic-usage)
2. [Command Line Options](#command-line-options)
3. [Configuration Files](#configuration-files)
4. [Ignore File](#ignore-file)
5. [Baseline Mode](#baseline-mode)
6. [CI/CD Integration](#cicd-integration)
7. [Outputs](#outputs)
8. [Exit Codes](#exit-codes)
9. [Testing & Demo](#testing--demo)

---

## Testing & Demo

The project includes a suite of vulnerable files across different languages to help you test the pipeline and see it in action.

### 1. Python Demo
```bash
git add test_vuln.py
python3 security_audit.py
```
*Expect: Detects SQL Injection in standard Python code.*

### 2. Async Python Demo
```bash
git add test_async.py
python3 security_audit.py
```
*Expect: Detects Command Injection inside asynchronous functions.*

### 3. JavaScript Demo
```bash
git add test_vuln.js
python3 security_audit.py
```
*Expect: Detects SQL Injection in Node.js code.*

### 4. Java Demo
```bash
git add test_vuln.java
python3 security_audit.py
```
*Expect: Detects SQL and Command Injection in Java methods.*

### 5. Go Demo
```bash
git add test_vuln.go
python3 security_audit.py
```
*Expect: Detects SQL Injection in Go packages.*

### 6. Full Web App Demo
```bash
git add vulnerable_app.py
python3 security_audit.py
```
*Expect: Detects Deserialization, Command Injection, and SQL Injection in a Flask application.*

---

## Security Features

### Secrets Detection (NEW)

The pipeline automatically scans for hardcoded secrets before analysis:

```python
# ❌ BAD - Will be detected
api_key = "sk_live_51H8xYzABC123456789"
aws_key = "AKIAIOSFODNN7EXAMPLE"

# ✅ GOOD - Use environment variables
api_key = os.getenv('API_KEY')
aws_key = os.getenv('AWS_ACCESS_KEY')
```

**Detected patterns:**
- Generic API keys
- AWS access/secret keys
- GitHub tokens (ghp_, gho_, etc.)
- Stripe keys (sk_live_, pk_test_)
- Private keys (RSA, DSA, EC)
- JWT tokens
- Passwords in URLs
- Hardcoded passwords

**Output example:**
```
⚠️  SECRETS DETECTED - DO NOT COMMIT
================================================================================
  STRIPE_KEY
  Location: payment.py:12
  Preview: sk_live_...789
  Line: stripe_key = "sk_live_51H8xYzABC123456789"

Recommendations:
  1. Remove secrets from code
  2. Use environment variables instead
  3. Add .env to .gitignore
  4. Rotate any exposed credentials
```

The scan is **non-blocking** - it warns but continues the security audit.

### API Resilience (NEW)

Production-ready error handling:

- **Automatic retry**: 3 attempts with exponential backoff (2s → 4s → 8s)
- **Graceful degradation**: Continues with 2/3 agents if one fails
- **Multi-model fallback**: Tries multiple Gemini models on rate limits
- **Comprehensive logging**: All failures tracked for debugging

**Example output:**
```
Agent A (Static Analysis - Gemini)...
  ⚠ gemini-2.0-flash rate limited, trying fallback...
  ✗ Agent A failed after 3 retries
⚠ Running with 2/3 agents (degraded mode)
⚠ Failed: Agent A
```

See [RESILIENCE.md](RESILIENCE.md) for technical details.

## Basic Usage

### Pre-Commit Hook (Recommended)

The tool runs automatically on `git commit`:

```bash
# Install hook
pre-commit install

# Make changes
git add file.py
git commit -m "add feature"
# → Security audit runs automatically
```

### Manual Execution

Run the audit manually:

```bash
# Analyze staged files
python security_audit.py

# With options
python security_audit.py --json --fail-on-high
```

---

## Command Line Options

### Output Options

```bash
# JSON output (for CI/CD, custom tooling)
python security_audit.py --json

# Summary only (fast feedback)
python security_audit.py --summary
```

### Exit Code Options

Control when to block commits:

```bash
# Default: fail on CRITICAL only
python security_audit.py

# Fail on HIGH or CRITICAL
python security_audit.py --fail-on-high

# Strict: fail on any vulnerability (CRITICAL, HIGH, MEDIUM, LOW)
python security_audit.py --strict

# Warn only: never block commits
python security_audit.py --warn-only
```

### Baseline Options

```bash
# Create or update baseline
python security_audit.py --baseline

# Custom baseline file location
python security_audit.py --baseline --baseline-file .baseline.json
```

### Performance Options

```bash
# Quick mode: skip debate and verification stages (~50% faster)
python security_audit.py --quick
```

### Configuration Options

```bash
# Custom config file
python security_audit.py --config custom-config.yaml

# Custom ignore file
python security_audit.py --ignore-file custom-ignore.txt
```

### Combined Options

All options work together:

```bash
python security_audit.py \
  --json \
  --fail-on-high \
  --baseline \
  --quick \
  --config .secaudit.yaml \
  --ignore-file .secaudit-ignore
```

---

## Configuration Files

### .secaudit.yaml

Configure file filters and scanning behavior:

```yaml
# Exclude patterns (glob syntax)
exclude:
  - 'test_*.py'
  - '*_test.py'
  - 'tests/**'
  - 'migrations/**'
  - '.venv/**'

# Include patterns (optional - if specified, only these are scanned)
# include:
#   - 'src/**'
#   - 'app/**'

# Minimum confidence level (LOW, MEDIUM, HIGH)
min_confidence: LOW

# Maximum line length before skipping (likely generated code)
max_line_length: 500
```

**Default Exclusions:**
- Test files: `test_*.py`, `*_test.py`, `tests/**`
- Migrations: `migrations/**`
- Virtual environments: `.venv/**`, `venv/**`, `env/**`
- Build artifacts: `__pycache__/**`, `build/**`, `dist/**`

**Creating Config:**
```bash
cp .secaudit.yaml.example .secaudit.yaml
# Edit as needed
```

---

## Ignore File

### .secaudit-ignore

Mark false positives to filter them out permanently:

```bash
# Format: filepath:line:VULN_TYPE  # optional comment

# Exact match
auth.py:47:SQL_INJECTION  # test code, safe

# Wildcard line number (ignore all occurrences in file)
utils.py:*:COMMAND_INJECTION  # all safe

# Just filename (portable across environments)
views.py:23:XSS  # sanitized elsewhere
```

**Supported Vulnerability Types:**
- `SQL_INJECTION`
- `XSS`
- `COMMAND_INJECTION`
- `PATH_TRAVERSAL`
- `INSECURE_DESERIALIZATION`
- `WEAK_CRYPTO`
- `HARDCODED_SECRET`
- `SSRF`
- `XXE`
- `LDAP_INJECTION`

**Creating Ignore File:**
```bash
cp .secaudit-ignore.example .secaudit-ignore
# Add your rules
```

**Workflow:**
1. Run audit, see false positive
2. Add to `.secaudit-ignore`: `file.py:42:SQL_INJECTION`
3. Run audit again - vulnerability filtered out
4. Commit ignore file to share with team

---

## Baseline Mode

Adopt security scanning on existing codebases without fixing everything first.

### First Run (Create Baseline)

```bash
# Create baseline with all current vulnerabilities
python security_audit.py --baseline

# Output:
# Baseline created with 47 vulnerability(ies)
# Baseline saved to .secaudit-baseline.json
```

This creates `.secaudit-baseline.json` with all current vulnerabilities.

### Subsequent Runs (Show Only New)

```bash
# Add new code
git add new_feature.py
git commit -m "add feature"

# Audit runs automatically (or manually)
python security_audit.py --baseline

# Output:
# Baseline mode: 2 new, 47 existing (suppressed)
# → Only shows 2 NEW vulnerabilities in new_feature.py
```

### Baseline File Management

**Option 1: Gitignore (Personal Baseline)**
```bash
# Add to .gitignore
echo ".secaudit-baseline.json" >> .gitignore
```
Each developer has their own baseline.

**Option 2: Commit (Team Baseline)**
```bash
# Commit baseline file
git add .secaudit-baseline.json
git commit -m "add security baseline"
```
Entire team shares the same baseline.

### Updating Baseline

```bash
# After fixing vulnerabilities, update baseline
python security_audit.py --baseline

# Baseline is automatically updated on each run
```

---

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/security.yml
name: Security Audit

on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Run security audit
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
        run: |
          python security_audit.py --json --fail-on-high
```

### GitLab CI

```yaml
# .gitlab-ci.yml
security_audit:
  stage: test
  image: python:3.9
  script:
    - pip install -r requirements.txt
    - python security_audit.py --json --fail-on-high
  variables:
    GEMINI_API_KEY: $GEMINI_API_KEY
    GROQ_API_KEY: $GROQ_API_KEY
```

### Jenkins

```groovy
pipeline {
    agent any
    stages {
        stage('Security Audit') {
            steps {
                sh 'pip install -r requirements.txt'
                sh 'python security_audit.py --json --fail-on-high'
            }
        }
    }
}
```

### JSON Output Parsing

```bash
# Save JSON output
python security_audit.py --json > results.json

# Parse with jq
cat results.json | jq '.summary'
cat results.json | jq '.vulnerabilities[] | select(.severity == "CRITICAL")'

# Count by severity
cat results.json | jq '.summary.critical'
```

---

## Outputs

After running the pipeline, check the `cache/` directory for detailed intermediate results.

### 1. Stage 1: Code Parsing (`cache/stage1_parsed.json`)

AST analysis of Python code:

```bash
# View parsed functions
cat cache/stage1_parsed.json | jq '.functions[]'

# View SQL patterns detected
cat cache/stage1_parsed.json | jq '.sql_patterns[]'

# View user input sources
cat cache/stage1_parsed.json | jq '.user_inputs[]'
```

**Structure:**
- `functions[]`: All function definitions with line numbers
- `sql_patterns[]`: SQL query construction patterns
- `user_inputs[]`: request.args, request.form, etc.
- `imports[]`: Import statements
- `file_operations[]`: open(), read(), write() calls
- `subprocess_calls[]`: subprocess.run(), os.system() calls

### 2. Stage 2: Multi-Agent Analysis (`cache/stage2_consensus.json`)

Findings from 3 security agents:

```bash
# View consensus findings
cat cache/stage2_consensus.json | jq '.consensus_findings[]'

# View high confidence vulnerabilities
cat cache/stage2_consensus.json | jq '.consensus_findings[] | select(.confidence=="HIGH")'
```

**Structure:**
- `agent_a_findings[]`: Static analysis (Gemini 2.0 Flash) - OWASP patterns
- `agent_b_findings[]`: Adversarial attacker (Groq Llama 3.1 8B) - exploitation perspective
- `agent_c_findings[]`: Defensive architect (Groq Llama 3.3 70B) - blast radius
- `consensus_findings[]`: 2/3 agreement threshold
  - `type`: SQL_INJECTION, XSS, COMMAND_INJECTION, etc.
  - `location`: File path and line number
  - `confidence`: HIGH (3/3) or MEDIUM (2/3)
  - `evidence`: Code snippet showing vulnerability

### 3. Stage 3: Severity Debate (`cache/stage3_debate.json`)

Severity classification after debate:

```bash
# View final severity rankings
cat cache/stage3_debate.json | jq '.final_rankings[]'

# View debate reasoning
cat cache/stage3_debate.json | jq '.debate_summary'
```

**Structure:**
- `final_rankings[]`: Vulnerabilities with adjusted severity
- `debate_summary`: Key points from severity discussion

### 4. Stage 4: Verification (`cache/stage4_verified.json`)

CWE cross-reference and attack trees:

```bash
# View CWE mappings
cat cache/stage4_verified.json | jq '.cwe_mappings[]'

# View attack trees
cat cache/stage4_verified.json | jq '.attack_trees[]'

# View mitigation advice
cat cache/stage4_verified.json | jq '.mitigations[]'
```

**Structure:**
- `cwe_mappings[]`: CWE IDs for each vulnerability
- `attack_trees[]`: Attack path visualization
- `mitigations[]`: Fix recommendations

---

## Exit Codes

The tool returns different exit codes based on findings:

| Exit Code | Meaning | When |
|-----------|---------|------|
| `0` | Clean | No vulnerabilities OR vulnerabilities below threshold |
| `1` | Vulnerabilities found | Vulnerabilities exceed configured threshold |
| `2` | Error | Tool error (not in git repo, parse error, etc.) |

### Exit Code Modes

**Default (--fail-on-critical):**
- Exit 0: No CRITICAL vulnerabilities
- Exit 1: CRITICAL vulnerabilities found
- HIGH, MEDIUM, LOW: allowed (exit 0)

**--fail-on-high:**
- Exit 0: No CRITICAL or HIGH vulnerabilities
- Exit 1: CRITICAL or HIGH vulnerabilities found
- MEDIUM, LOW: allowed (exit 0)

**--strict:**
- Exit 0: No vulnerabilities at all
- Exit 1: Any vulnerability found (CRITICAL, HIGH, MEDIUM, LOW)

**--warn-only:**
- Exit 0: Always (never blocks)
- Shows vulnerabilities but never fails

### CI/CD Policy Examples

**Strict Policy (Block Everything):**
```bash
python security_audit.py --strict
```

**Balanced Policy (Block High+Critical):**
```bash
python security_audit.py --fail-on-high
```

**Gradual Adoption (Warn Only):**
```bash
# Phase 1: Warn only, don't block
python security_audit.py --warn-only

# Phase 2: Block critical only
python security_audit.py --fail-on-critical

# Phase 3: Block high and critical
python security_audit.py --fail-on-high
```

---

## Examples

### Example 1: Local Development

```bash
# Install hook
pre-commit install

# Work normally
git add feature.py
git commit -m "add feature"
# → Audit runs, blocks if critical vulnerabilities found
```

### Example 2: Existing Codebase

```bash
# Create baseline (don't fix 100 vulnerabilities first)
python security_audit.py --baseline

# Work on new features
git add new_feature.py
git commit -m "add feature"
# → Only shows vulnerabilities in new_feature.py
```

### Example 3: CI/CD Pipeline

```bash
# In CI/CD script
python security_audit.py --json --fail-on-high > results.json

# Parse results
CRITICAL=$(cat results.json | jq '.summary.critical')
if [ "$CRITICAL" -gt 0 ]; then
  echo "Critical vulnerabilities found!"
  exit 1
fi
```

### Example 4: False Positive Management

```bash
# Run audit
python security_audit.py
# → Shows: auth.py:47:SQL_INJECTION

# Review finding - it's a false positive
# Add to ignore file
echo "auth.py:47:SQL_INJECTION  # test code" >> .secaudit-ignore

# Run again
python security_audit.py
# → Vulnerability filtered out
```

---

## Troubleshooting

### "Not a git repository"

The tool requires a git repository. Initialize one:
```bash
git init
```

### "No Python files staged"

Stage some Python files:
```bash
git add *.py
```

### API Rate Limits

Free tier APIs have generous limits:
- **Gemini 2.0 Flash**: 15 requests per minute (sufficient for most workflows)
- **Groq Llama 3.1 8B**: 14,400 requests per day
- **Groq Llama 3.3 70B**: 14,400 requests per day

Typical usage (10-50 commits/day) stays well within limits.

If you hit rate limits:
- Use `--quick` mode for faster scans
- Space out commits
- Consider caching strategies

### False Positives

Add to `.secaudit-ignore` file:
```bash
filepath:line:VULN_TYPE  # reason
```

### Performance Issues

- Use `--quick` mode (skips stages 3-4)
- Configure file filters in `.secaudit.yaml`
- Exclude test files, migrations, generated code

---

## Best Practices

1. **Start with baseline mode** on existing codebases
2. **Commit ignore file** to share false positive decisions with team
3. **Use --fail-on-high** in CI/CD for balanced security
4. **Review findings** before adding to ignore file
5. **Update baseline** after fixing vulnerabilities
6. **Configure file filters** to reduce noise
7. **Use JSON output** for custom integrations

---

## Getting Help

```bash
# Show help
python security_audit.py --help

# View examples
python security_audit.py --help | grep -A 20 "Examples:"
```

For issues or questions, open an issue on GitHub.
