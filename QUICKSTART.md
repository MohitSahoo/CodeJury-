# Security Audit Pipeline - Quick Start

## Setup (5 minutes)

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Configure API keys:**
```bash
cp .env.example .env
# Edit .env and add your API keys:
# - GEMINI_API_KEY (get from https://makersuite.google.com/app/apikey)
# - GROQ_API_KEY (get from https://console.groq.com/keys)
```

3. **Test installation:**
```bash
python -c "import google.generativeai; import groq; print('✓ All imports work')"
```

## Usage

### Install Pre-Commit Hook

```bash
pre-commit install
```

### Test with Vulnerable Code

Create a test file with a vulnerability:

```python
# test_vuln.py
import sqlite3
from flask import request

def login(username, password):
    # SQL Injection vulnerability
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    conn = sqlite3.connect('db.sqlite')
    cursor = conn.cursor()
    cursor.execute(query)
    return cursor.fetchone()
```

Stage and commit:

```bash
git add test_vuln.py
git commit -m "test security audit"
```

Expected: Security audit runs, detects SQL injection, blocks commit.

### Run Manually (Without Git Hook)

```bash
python security_audit.py
```

### Force Re-run (Clear Cache)

```bash
rm -rf cache/
python security_audit.py
```

## Test Individual Stages

### Stage 1: Code Parsing
```bash
python test_stage1.py
```

### Stage 2: Multi-Agent Analysis
```bash
python test_stage2.py
# Requires Stage 1 cache to exist
```

### Stages 3 & 4: Debate and Verification
```bash
python test_stage34.py
# Requires Stages 1-2 cache to exist
```

### Full Pipeline Test
```bash
python test_full_pipeline.py
```

## Output

Terminal report shows:
- Vulnerability summary (critical/high/medium/low counts)
- Detailed findings with CWE IDs
- Attack tree visualization
- Mitigation advice

Intermediate cache:
- `cache/stage1_parsed.json` - AST analysis
- `cache/stage2_consensus.json` - Multi-agent findings
- `cache/stage3_debate.json` - Severity debate
- `cache/stage4_verified.json` - CWE verification + attack trees

## Troubleshooting

### "GEMINI_API_KEY not found"
- Check `.env` file exists and has valid key
- Run: `cat .env | grep GEMINI_API_KEY`

### "No Python files in git diff"
- Stage Python files first: `git add *.py`
- Or run manually: `python security_audit.py`

### "Rate limit exceeded"
- Gemini: 15 RPM free tier
- Groq: 30 RPM free tier
- Wait and retry, or upgrade API tier

### Agent failures
- Tool gracefully degrades to 2-agent consensus if one agent fails
- Check API keys are valid
- Check network connectivity

## Token Budget

Per commit (average):
- Gemini: ~0.4K tokens
- Groq: ~0.2K tokens
- Claude: ~0.2K tokens (heuristics only in MVP)
- **Total: ~0.6K tokens** (well within free tier)

Safe to run 1000+ commits/day on free tier.

## Exit Codes

- `0` - No vulnerabilities (commit proceeds)
- `1` - Critical vulnerabilities found (commit blocked)
- `2` - Error during analysis (commit proceeds with warning)

## Customization

Edit agent prompts in:
- `agents/security_agents.py` - Multi-agent analysis
- `agents/debate_room.py` - Severity debate
- `tools/cwe_database.py` - Vulnerability patterns

## Next Steps

1. Run pipeline on real code
2. Review terminal output
3. Fix vulnerabilities
4. Commit again (should pass)

For detailed implementation notes, see `IMPLEMENTATION_COMPLETE.md`.
