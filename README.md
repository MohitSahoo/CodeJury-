# Security Audit Pipeline

**Status: ✅ MVP Complete - All 5 Stages Working**

Multi-agent security analysis for Python code via pre-commit hook.

## Features

✅ **Multi-Agent Consensus**
- 3 security agents with different perspectives
- 2/3 consensus threshold (reduces false positives)
- Static analysis + adversarial + defensive viewpoints

✅ **Token Optimized**
- Function-level analysis (not full files)
- Skip debate if code is clean
- Single verification pass
- ~2.2K tokens avg per commit

✅ **Rich Terminal UI**
- Color-coded severity badges
- Attack tree visualization
- CWE database cross-reference
- Exit codes (0=clean, 1=block, 2=error)

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure API Keys
```bash
cp .env.example .env
# Edit .env and add:
# - GEMINI_API_KEY (from https://makersuite.google.com/app/apikey)
# - GROQ_API_KEY (from https://console.groq.com/keys)
```

### 3. Install Pre-Commit Hook
```bash
pre-commit install
```

### 4. Test
Create a test file with a vulnerability:

```python
# test_vuln.py
import sqlite3

def login(username, password):
    query = f"SELECT * FROM users WHERE username='{username}'"
    conn = sqlite3.connect('db.sqlite')
    cursor = conn.cursor()
    cursor.execute(query)
    return cursor.fetchone()
```

Stage and commit:

```bash
git add test_vuln.py
git commit -m "test"
```

Expected: Security audit runs, detects SQL injection, blocks commit.

## Documentation

- **[SECURITY_AUDIT_PLAN.md](../SECURITY_AUDIT_PLAN.md)** - Full implementation plan
- **[CLAUDE.md](CLAUDE.md)** - Security audit configuration

## Project Structure

```
security-audit-pipeline/
├── security_audit.py           # CLI entry point
├── orchestrator.py             # Main pipeline orchestrator
├── agents/
│   ├── code_parser.py          # Stage 1: AST parsing
│   ├── security_agents.py      # Stage 2: Multi-agent analysis
│   ├── debate_room.py          # Stage 3: Severity debate
│   └── verifier.py             # Stage 4: CWE + attack trees
├── tools/
│   ├── git_diff_extractor.py   # Git integration
│   ├── consensus_scorer.py     # 2/3 consensus logic
│   ├── token_tracker.py        # Usage tracking
│   ├── attack_tree_builder.py  # Attack path visualization
│   └── cwe_database.py         # Vulnerability database
├── outputs/                    # Reports (generated)
└── cache/                      # Stage results (generated)
```

## Token Budget

| Scenario | Gemini | Groq | Claude | Total |
|----------|--------|------|--------|-------|
| Clean code (80%) | 0 | 0 | 1K | 1K |
| Vuln found (20%) | 2K | 1K | 4K | 7K |
| **Average** | **0.4K** | **0.2K** | **1.6K** | **2.2K** |

**Free tier capacity:** 2,500+ commits/day

## Exit Codes

- `0` - No vulnerabilities (commit proceeds)
- `1` - Critical vulnerabilities found (commit blocked)
- `2` - Error during analysis (commit proceeds with warning)

## Implementation Status

- [x] Session 1: Project scaffold + git integration
- [x] Session 2: Stage 1 - Code parsing (AST analysis)
- [x] Session 3: Stage 2 - Multi-agent analysis (2-agent consensus)
- [x] Session 4: Stages 3-4 - Debate + verification + attack trees
- [x] Session 5: Stage 5 - Terminal UI + orchestrator + end-to-end

**Working MVP with 2-agent consensus (Groq + Claude heuristic).**

## Scope

- **Language:** Python only (MVP)
- **Workflow:** Pre-commit hook (30s runtime accepted)
- **Consensus:** 2/3 agents (balanced approach)
- **Output:** Terminal UI with Rich library
- **Attack trees:** Single-file scope only

## Architecture

```
Git Diff (changed Python files)
     ↓
[Stage 1: Code Parsing]
  Python AST → extract functions, SQL queries, user inputs
     ↓
[Stage 2: Multi-Agent Analysis]
  Agent A: Static analysis (Gemini) - OWASP patterns
  Agent B: Adversarial attacker (Groq) - exploitation perspective
  Agent C: Defensive architect (Claude) - blast radius
  → Consensus scoring (2/3 threshold)
     ↓
[Stage 3: Severity Debate] (ONLY if vulns found)
  Skeptic vs Advocate → severity ranking
     ↓
[Stage 4: Verification] (single pass)
  Cross-check CWE database
  Generate attack tree (single-file scope)
     ↓
[Stage 5: Terminal Report]
  Rich UI with colors, severity badges, attack tree
     ↓
Exit 1 if critical vuln (blocks commit)
```

## License

MIT
