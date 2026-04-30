# Security Audit Pipeline

**Security scanner you won't disable after day 1.**

Multi-agent AI consensus catches vulnerabilities single tools miss, with fewer false positives than traditional scanners. Free tier friendly, <30s per commit.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)

---

## Why This?

**The Problem:** Traditional security scanners have high false positive rates (developers disable them) OR miss critical vulnerabilities (single-perspective analysis).

**The Solution:** 3 AI agents debate every commit from different perspectives:
- **Agent A (Static Analysis):** OWASP Top 10 patterns
- **Agent B (Adversarial Attacker):** "How would I exploit this?"
- **Agent C (Defensive Architect):** Blast radius assessment

**2/3 consensus threshold** = fewer false positives. **Multi-perspective analysis** = better detection.

---

## Quick Start

### 1. Install
```bash
pip install -r requirements.txt
```

### 2. Configure API Keys
```bash
cp .env.example .env
# Add your keys:
# - GEMINI_API_KEY (from https://makersuite.google.com/app/apikey)
# - GROQ_API_KEY (from https://console.groq.com/keys)
```

### 3. Install Pre-Commit Hook
```bash
pre-commit install
```

### 4. Test
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

```bash
git add test_vuln.py
git commit -m "test"
# → Security audit runs, detects SQL injection, blocks commit
```

---

## Architecture

The pipeline uses a decoupled, 5-stage orchestration model designed for high performance and accurate consensus.

```mermaid
graph TD
    subgraph "Input Layer"
        Git[Git Diff] --> EP[Extractor / Parser]
        Config[Config Manager] --> EP
    end

    subgraph "Stage 1: Parsing"
        EP --> AST[AST Analysis]
        AST --> Hash[Content Hashing]
        Hash --> Cache1[(Stage 1 Cache)]
    end

    subgraph "Stage 2: Analysis (The Consensus Engine)"
        Cache1 --> AgA[Agent A: Static Analysis]
        Cache1 --> AgB[Agent B: Adversarial Attacker]
        Cache1 --> AgC[Agent C: Defensive Architect]
        AgA & AgB & AgC --> Cons[Consensus Scorer]
        Cons --> Cache2[(Consensus Cache)]
    end

    subgraph "Stage 3 & 4: Refinement"
        Cache2 --> Debate[Severity Debate]
        Debate --> Verif[CWE Verification]
        Verif --> Trees[Attack Tree Generation]
    end

    subgraph "Output Layer"
        Trees --> Report[Terminal Reporter]
        Report --> JSON[JSON Output]
        Report --> Console[Rich Console UI]
    end

    style AgA fill:#4285F4,color:#fff
    style AgB fill:#F4B400,color:#fff
    style AgC fill:#0F9D58,color:#fff
```

---

## Features

### ✅ Multi-Language Support
- **Python**: Deep AST analysis (supports `async def`)
- **JavaScript**: Function and SQL pattern extraction
- **Java**: Method-level security analysis
- **Go**: Package-level pattern recognition
- *Designed for easy extension via `ParserFactory`*

### ✅ Multi-Agent Consensus
- 3 security agents (Gemini, Groq/Llama3, Claude/Patterns)
- 2/3 consensus threshold (reduces false positives)
- Graceful degradation with automatic 2-agent fallback

### ✅ Intelligent Caching
- **Content-Aware**: Uses git blob hashes to track changes
- **Granular**: Individual stages are cached independently
- **Fast**: <1s for re-runs with no changes

### ✅ Token Optimized
- **0.6K tokens avg per commit**
- Function-level analysis (not full files)
- Skips clean code automatically

### ✅ Rich Terminal UI
- Color-coded severity badges (🔴 Critical, 🟠 High, 🟡 Medium, 🔵 Low)
- Attack tree visualization showing exploitation paths
- CWE database cross-reference

### ✅ Pre-Commit Integration
- Blocks commits with critical vulnerabilities
- Exit code 0 (clean) allows commit
- Exit code 1 (critical) blocks commit
- <30s runtime per commit

### ✅ Production-Ready Features
- **Ignore file** - Mark false positives once, never see again (`.secaudit-ignore`)
- **Baseline mode** - Adopt on existing codebases, only show new vulnerabilities
- **JSON output** - CI/CD integration, custom tooling, dashboards
- **File filters** - Skip tests, migrations, generated code automatically
- **Exit code modes** - Configurable severity thresholds (critical, high, strict, warn-only)

---

## Advanced Usage

### Ignore False Positives

Create `.secaudit-ignore` to mark false positives:

```bash
# .secaudit-ignore
# Format: filepath:line:VULN_TYPE  # optional comment

auth.py:47:SQL_INJECTION  # test code, safe
views.py:23:XSS  # input sanitized elsewhere
utils.py:*:COMMAND_INJECTION  # ignore all in this file
```

Ignored vulnerabilities are filtered out automatically. No more noise from known false positives.

### Baseline Mode (Existing Codebases)

Adopt security scanning on existing projects without fixing 100 vulnerabilities first:

```bash
# First run - create baseline
python security_audit.py --baseline

# Subsequent runs - only show NEW vulnerabilities
git add new_feature.py
git commit -m "add feature"
# → Only shows vulnerabilities in new_feature.py
```

Baseline stored in `.secaudit-baseline.json`. Add to `.gitignore` or commit for team-wide baseline.

### JSON Output (CI/CD Integration)

Output results as JSON for custom tooling:

```bash
# JSON output
python security_audit.py --json

# Example output:
{
  "summary": {
    "total": 3,
    "critical": 1,
    "high": 1,
    "medium": 1,
    "low": 0
  },
  "vulnerabilities": [
    {
      "file": "auth.py",
      "type": "SQL_INJECTION",
      "location": "auth.py:47",
      "severity": "CRITICAL",
      "description": "...",
      "mitigation": "..."
    }
  ]
}
```

Use in CI/CD pipelines, dashboards, or custom integrations.

### File Filters (Reduce Noise)

Create `.secaudit.yaml` to exclude test files, migrations, generated code:

```yaml
# .secaudit.yaml
exclude:
  - 'test_*.py'
  - '*_test.py'
  - 'tests/**'
  - 'migrations/**'
  - '__generated__/**'
  - '.venv/**'

# Optional: only scan specific directories
# include:
#   - 'src/**'
#   - 'app/**'

min_confidence: LOW
max_line_length: 500
```

Default config excludes common patterns automatically.

### Exit Code Modes (CI/CD Policies)

Control when to block commits based on severity:

```bash
# Default: fail on CRITICAL only
python security_audit.py

# Fail on HIGH or CRITICAL
python security_audit.py --fail-on-high

# Strict: fail on any vulnerability
python security_audit.py --strict

# Warn only: never block commits
python security_audit.py --warn-only
```

Different teams need different policies. Choose what works for you.

### Quick Mode (Fast Feedback)

Skip debate and verification stages for faster results:

```bash
python security_audit.py --quick
# → Skips stages 3-4, ~50% faster
```

Less accurate but useful for rapid iteration.

### Combined Usage

All flags work together:

```bash
# CI/CD pipeline example
python security_audit.py \
  --json \
  --fail-on-high \
  --baseline \
  --quick
```

---

## Comparison

| Feature | This Tool | Bandit | Semgrep | Snyk |
|---------|-----------|--------|---------|------|
| **Multi-agent consensus** | ✅ 3 agents | ❌ Single | ❌ Single | ❌ Single |
| **False positive rate** | Low (2/3 threshold) | High | Medium | Low |
| **Attack tree visualization** | ✅ | ❌ | ❌ | ✅ (paid) |
| **Ignore file support** | ✅ | ✅ | ✅ | ✅ |
| **Baseline mode** | ✅ | ❌ | ❌ | ✅ (paid) |
| **JSON output** | ✅ | ✅ | ✅ | ✅ |
| **File filters** | ✅ | ✅ | ✅ | ✅ |
| **Configurable exit codes** | ✅ | Limited | Limited | ✅ |
| **Free tier** | Unlimited | ✅ | 10 scans/mo | 200 tests/mo |
| **Pre-commit hook** | ✅ | ✅ | ✅ | ❌ |
| **Token cost per commit** | 0.6K (~$0.0001) | N/A | N/A | N/A |
| **Languages** | Python (MVP) | Python | 30+ | 30+ |
| **Setup time** | 5 minutes | 2 minutes | 5 minutes | 10 minutes |

**Why multi-agent?** Single-tool scanners optimize for one perspective. Multi-agent consensus catches what single tools miss while filtering out noise.

---

## How It Works

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
  Adjust severity based on confidence
     ↓
[Stage 4: Verification]
  Cross-check CWE database
  Generate attack tree (single-file scope)
     ↓
[Stage 5: Terminal Report]
  Rich UI with colors, severity badges, attack tree
     ↓
Exit 1 if critical vuln (blocks commit)
```

**Token Budget (Actual):**
- Clean code (80% of commits): 0 tokens
- Vuln found (20% of commits): ~3K tokens
- **Average: 0.6K tokens per commit**

---

## Example Output

```
Security Audit Results
⚠ 2 vulnerabilities found
Critical: 0  High: 2  Medium: 0  Low: 0

SQL_INJECTION
Location: auth.py:47
Severity: HIGH (Confidence: MEDIUM - 2/3 agents agree)
CWE: CWE-89 - Improper Neutralization of Special Elements

Evidence:
  query = f"SELECT * FROM users WHERE username='{username}'"

Attack Tree:
🎯 Compromise system via SQL injection
└── SQL_INJECTION (MEDIUM difficulty, 15-30 minutes)
    ├── 1. Identify SQL injection at auth.py:47
    ├── 2. Craft malicious SQL payload (e.g., ' OR '1'='1)
    ├── 3. Bypass authentication or extract data
    └── 4. Escalate to full database access

Mitigation:
  Use parameterized queries:
  cursor.execute("SELECT * FROM users WHERE username=?", (username,))

XSS
Location: views.py:23
Severity: HIGH (Confidence: MEDIUM - 2/3 agents agree)
CWE: CWE-79 - Cross-Site Scripting
...
```

---

## Who Is This For?

### ✅ Solo SaaS Founders
Building MVP, no security budget, terrified of breaches. **Catches SQL injection before your first customer gets hacked.**

### ✅ Open Source Maintainers
Reviewing PRs, can't manually audit every line. **Automated security review on every PR, blocks merges with critical vulns.**

### ✅ Bootcamp Grads / Learners
Learning security, want instant feedback. **Learn security by doing - see attack trees for every vuln you write.**

---

## Documentation

- **[USAGE.md](USAGE.md)** - Detailed usage and examples
- **[STATUS.md](STATUS.md)** - Implementation status and roadmap

---

## Project Structure

```
security-audit-pipeline/
├── security_audit.py           # CLI entry point with argument parsing
├── orchestrator.py             # Main pipeline orchestrator
├── agents/
│   ├── code_parser.py          # Stage 1: AST parsing
│   ├── security_agents.py      # Stage 2: Multi-agent analysis
│   ├── debate_room.py          # Stage 3: Severity debate
│   ├── verifier.py             # Stage 4: CWE + attack trees
│   └── terminal_reporter.py    # Stage 5: Terminal UI + JSON output
├── tools/
│   ├── git_diff_extractor.py   # Git integration
│   ├── security_consensus.py   # Consensus scoring
│   ├── cwe_database.py         # Vulnerability database
│   ├── attack_tree_builder.py  # Attack path visualization
│   ├── token_tracker.py        # Usage tracking
│   ├── ignore_filter.py        # False positive filtering
│   ├── baseline_manager.py     # Incremental adoption
│   └── config_manager.py       # File filters and config
└── tests/                      # Test suite
    ├── test_ignore_filter.py
    ├── test_baseline_manager.py
    ├── test_config_manager.py
    └── test_integration.py
```

---

## Roadmap

### MVP (Current)
- [x] Python support
- [x] Pre-commit hook
- [x] Multi-agent consensus (2/3 threshold)
- [x] Attack tree visualization
- [x] CWE database integration
- [x] Rich terminal UI
- [x] Ignore file support (`.secaudit-ignore`)
- [x] Baseline mode (incremental adoption)
- [x] JSON output (CI/CD integration)
- [x] File filters (`.secaudit.yaml`)
- [x] Configurable exit codes (fail-on-high, strict, warn-only)

### Next
- [ ] JavaScript/TypeScript support
- [ ] GitHub Action (alternative to pre-commit)
- [ ] Cross-file attack trees
- [ ] Auto-fix suggestions (generate patches)
- [ ] Web dashboard with D3.js visualizations
- [ ] Custom rule definitions
- [ ] SARIF output format
- [ ] IDE integrations (VS Code, PyCharm)

---

## Known Limitations

1. **Agent C uses heuristics** - Pattern-based detection for the defensive perspective in the current version.
2. **Local Scope** - No cross-file attack chains yet (requires full codebase context).
3. **API Limits** - Free tier APIs may occasionally hit rate limits; the pipeline handles this via 2-agent fallback.

---

## Contributing

Contributions welcome! Areas where help is needed:
- Language support (JavaScript/TypeScript, Go, Rust)
- Additional vulnerability patterns
- False positive reduction
- Performance optimization
- Documentation improvements

---

## FAQ

**Q: How accurate is it?**
A: 2/3 consensus threshold reduces false positives vs single-tool scanners. Tested on multiple Python projects with good detection rates.

**Q: Does it slow down commits?**
A: <30s per commit. Acceptable for most workflows. Skips clean code automatically. Use `--quick` for ~50% faster results.

**Q: What if I disagree with a finding?**
A: Add it to `.secaudit-ignore` file. Format: `filepath:line:VULN_TYPE`. The vulnerability will be filtered out on future runs.

**Q: Can I use this on an existing codebase with many vulnerabilities?**
A: Yes! Use `--baseline` mode. First run creates a baseline, subsequent runs only show NEW vulnerabilities. Adopt incrementally without fixing everything first.

**Q: Can I use this in CI/CD?**
A: Yes. Use `--json` for structured output and `--fail-on-high` or `--strict` for exit code control. Example:
```bash
python security_audit.py --json --fail-on-high
```

**Q: How do I exclude test files?**
A: Create `.secaudit.yaml` with exclude patterns. Test files, migrations, and common patterns are excluded by default.

**Q: What about other languages?**
A: MVP is Python only. Architecture designed for easy extension to JS/TS, Go, etc. Contributions welcome.

**Q: How much does it cost?**
A: Free tier APIs (Gemini + Groq). ~0.6K tokens per commit = ~$0.0001 per commit. 1000+ commits/day on free tier.

---

## License

MIT

---

**Star this repo if you find it useful!** ⭐
