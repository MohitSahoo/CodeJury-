# Security Audit Pipeline - Product Requirements Document (PRD)

**Version:** 1.2  
**Date:** April 2025  
**Status:** MVP Complete - All Free-Tier APIs  
**Author:** Product Team  
**Audience:** Engineering, Security, DevOps

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Problem Statement & Opportunity](#problem-statement--opportunity)
3. [Product Vision & Goals](#product-vision--goals)
4. [Core Requirements](#core-requirements)
5. [Technical Architecture](#technical-architecture)
6. [Agent Framework & API Strategy](#agent-framework--api-strategy)
7. [MVP Scope & Phasing](#mvp-scope--phasing)
8. [Success Metrics](#success-metrics)
9. [Timeline & Milestones](#timeline--milestones)

---

## Executive Summary

**Security Audit Pipeline** is a pre-commit security scanner that uses multi-agent AI consensus to catch vulnerabilities with fewer false positives than traditional single-tool scanners. Instead of relying on one analysis perspective, the pipeline orchestrates 3 independent security agents that debate every commit, requiring 2 out of 3 to flag an issue before blocking a commit.

The product targets solo founders, open-source maintainers, and bootcamp graduates who need fast, reliable security feedback without the noise of traditional static analysis tools.

### Key Differentiators

- **2/3 consensus threshold** reduces false positives by filtering single-perspective detections
- **Multi-perspective analysis** (Static, Adversarial, Defensive) catches vulnerabilities that single tools miss
- **Free tier friendly** (0.6K tokens/commit, ~$0.0001/commit)
- **Fast execution** (<30s per commit, <1s with caching)
- **Incremental adoption** via baseline mode (no need to fix 100 vulnerabilities first)

---

## Problem Statement & Opportunity

### The Problem

Traditional security scanners have two extremes:

#### 1. High False Positive Rate → Developers disable them after day 1

Tools like Bandit generate noise (30%+ false positives), leading developers to ignore findings or disable pre-commit hooks entirely.

#### 2. Miss Critical Vulnerabilities → Single-perspective analysis has blind spots

A static analysis tool optimized for pattern matching misses logical flaws that an adversarial attacker would exploit.

### Target User Pain

- **Solo Founders:** Terrified of breaches, no budget for security consultants
- **Open Source Maintainers:** Can't manually audit every PR, need automated review
- **Bootcamp Graduates:** Want to learn security, need instant feedback loops

### Opportunity

Multi-agent AI consensus enables a new category of security tooling: **accurate without the noise, comprehensive without the cost.** By orchestrating 3 agents to debate vulnerabilities, we can achieve >90% precision (users trust findings) while maintaining high recall (we catch what single tools miss).

---

## Product Vision & Goals

### Vision

**A security scanner developers won't disable.** Multi-agent consensus catches vulnerabilities single tools miss, with fewer false positives, in <30s per commit, for free.

### Goals (OKRs)

#### Goal 1: Achieve >90% Precision (Users Trust Findings)

- **KR1:** <10% false positive rate (measured on test suites)
- **KR2:** >80% developer satisfaction (findings are actionable)

#### Goal 2: Fast & Free (Accessible to All Teams)

- **KR1:** <30s execution time per commit
- **KR2:** 0.6K tokens/commit on free tier APIs

#### Goal 3: Easy Adoption (Works on Existing Codebases)

- **KR1:** Baseline mode enables adoption without fixing 100 vulns first
- **KR2:** <5 minutes from install to first scan

---

## Core Requirements

### Functional Requirements

#### FR1: Multi-Agent Analysis

The system SHALL orchestrate 3 independent security agents analyzing the same code from different perspectives:

- **Agent A (Static Analysis):** OWASP Top 10 patterns, known CVE signatures
- **Agent B (Adversarial Attacker):** How would I exploit this? Privilege escalation, data exfiltration
- **Agent C (Defensive Architect):** Blast radius, impact assessment, compensating controls

**Consensus:** 2 out of 3 agents must flag an issue for it to be reported.

#### FR2: Code Parsing

The system SHALL parse the following languages with AST-level analysis:

- **Python:** Function extraction, SQL pattern detection, async/await support
- **JavaScript:** Function boundaries, SQL injection patterns
- **Java:** Method-level analysis
- **Go:** Package-level pattern recognition

#### FR3: Vulnerability Detection

The system SHALL detect the following vulnerability categories:

- SQL Injection
- Cross-Site Scripting (XSS)
- Command Injection
- Hard-coded Credentials
- Insecure Deserialization
- Path Traversal
- Broken Authentication

#### FR4: Pre-Commit Integration

- Exit code 0 (success): No critical vulnerabilities, commit allowed
- Exit code 1 (failure): Critical vulnerabilities found, commit blocked
- Configurable fail thresholds: critical, high, strict, warn-only

#### FR5: False Positive Management

- Ignore file (`.secaudit-ignore`) for suppressing known false positives
- Baseline mode for incremental adoption on existing projects
- File filters (`.secaudit.yaml`) to exclude test, migration, generated code

#### FR6: Reporting & Output

- Rich terminal UI with color-coded severity badges
- Attack tree visualization (single-file scope, shows exploitation paths)
- JSON output for CI/CD integration
- CWE database cross-reference

### Non-Functional Requirements

#### NFR1: Performance

- **Clean code (no vulnerabilities):** <1s, leveraging cache
- **Vulnerable code found:** ~3K tokens, <30s total
- **Average per commit:** 0.6K tokens

#### NFR2: Reliability

- Graceful degradation if API #2 fails (fallback to 2-agent consensus)
- Resilient caching to avoid repeated API calls

#### NFR3: Usability

- **Setup time:** <5 minutes (install dependencies, add hook)
- **Clear, actionable output** (not overwhelming)

---

## Technical Architecture

### 5-Stage Pipeline

#### Stage 1: Code Parsing & Extraction

- **Input:** Git diff (changed files)
- **Process:** AST analysis, function extraction, SQL pattern detection
- **Output:** Structured code snippets for agents
- **Cache:** Content-hashed blobs for fast re-runs

#### Stage 2: Multi-Agent Analysis (Consensus Engine)

- **Agent A:** Static analyzer (pattern matching)
- **Agent B:** Adversarial attacker (exploitation thinking)
- **Agent C:** Defensive architect (blast radius)
- **Consensus:** 2/3 threshold

#### Stage 3: Severity Debate (If Vulnerabilities Found)

Agents debate severity adjustments based on confidence levels.

#### Stage 4: Verification & Attack Tree Generation

- Cross-check against CWE database
- Generate attack tree (single-file scope)

#### Stage 5: Terminal Report & Output

- Rich terminal UI with colors
- JSON output
- Exit code (configurable by severity)

---

## Agent Framework & API Strategy

### Agent Configuration

| Agent | Provider | Model | Perspective | Free Tier | Status |
|-------|----------|-------|-------------|-----------|--------|
| **Agent A** | Google Gemini | gemini-2.0-flash-exp | Static Analysis | ✓ Yes | ✅ Working |
| **Agent B** | Groq | llama-3.1-8b-instant | Adversarial | ✓ Yes | ✅ Working |
| **Agent C** | Groq | llama-3.3-70b-versatile | Defensive | ✓ Yes | ✅ Working |

### Multi-Model Strategy

All three agents use **free-tier APIs** with different models for diverse perspectives:

- **Agent A (Gemini)**: Google's multimodal model, strong at pattern recognition and OWASP compliance
- **Agent B (Groq Llama 3.1 8B)**: Fast, lightweight model optimized for adversarial thinking
- **Agent C (Groq Llama 3.3 70B)**: Larger model for deeper defensive analysis and blast radius assessment

**Why two Groq models?**
- Different model sizes provide different reasoning depths
- Llama 3.1 8B: fast, aggressive attack surface analysis
- Llama 3.3 70B: thorough, defensive architecture review
- Both free on Groq's generous tier
- No additional API keys needed

---

## MVP Scope & Phasing

### Phase 1: MVP (Python-Only, Free APIs)

**Status:** ✅ Complete

#### Implemented Features

- ✅ Python code parsing (AST-based)
- ✅ 3-agent consensus (Gemini, Groq Llama 3.1 8B, Groq Llama 3.3 70B)
- ✅ SQL Injection, XSS, Command Injection, Hard-coded Secrets detection
- ✅ Pre-commit hook integration
- ✅ Ignore file (`.secaudit-ignore`)
- ✅ Baseline mode (for existing codebases)
- ✅ Rich terminal output
- ✅ JSON output
- ✅ Configurable exit codes (critical, high, strict, warn-only)
- ✅ File filters (`.secaudit.yaml`)
- ✅ JavaScript/TypeScript support (added)
- ✅ Go, Java support (added)
- ✅ Cross-file taint analysis (added)
- ✅ Attack chain visualization (added)

#### Out of Scope (Future Phases)

- Auto-fix suggestions
- IDE integrations
- Web dashboard

### Phase 2: Expand (Post-MVP)

**Status:** ✅ Complete

- ✅ JavaScript/TypeScript support
- ✅ Go, Java support
- ✅ Cross-file attack chain analysis
- ⏳ GitHub Actions alternative to pre-commit (planned)
- ⏳ Web dashboard with D3.js visualization (planned)

### Phase 3: Advanced (Future)

- ⏳ Auto-fix patches
- ⏳ Custom rule definitions
- ⏳ VS Code, PyCharm plugins
- ⏳ GitHub Actions integration

---

## Success Metrics

### Technical Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Precision** | >90% (TP / TP+FP) | Manual review on test suite |
| **Recall** | >80% (TP / TP+FN) | Manual review on known vulns |
| **Execution Speed** | <30s per commit | Timer on production runs |
| **Token Usage** | 0.6K avg per commit | API usage logs |
| **Cache Hit Rate** | >70% for unchanged code | Internal metrics |

### User Satisfaction Metrics

- **Adoption:** ≥100 GitHub stars in 3 months
- **Developer satisfaction:** ≥4/5 on usefulness (survey)
- **False positive complaints:** <5% of findings
- **Setup complaints:** <2% (too hard to install)

### Cost Metrics

- **Cost per commit:** <$0.001
- **Monthly cost (1,000 commits):** <$1
- **Free tier utilization:** 80-90%

---

## Timeline & Milestones

### Development Status

**MVP Phase (Complete)** ✅
- All core features implemented
- 3-agent consensus working (Gemini, Groq Llama 3.1 8B, Groq Llama 3.3 70B)
- Multi-language support (Python, JavaScript, TypeScript, Go, Java)
- Cross-file taint analysis and attack chain visualization
- Pre-commit hook integration
- Baseline mode and ignore filters

**Phase 2 (Mostly Complete)** ✅
- Multi-language parsers implemented
- Cross-file analysis working
- Remaining: GitHub Actions integration, Web dashboard

**Phase 3 (Planned)** ⏳
- Auto-fix suggestions
- IDE plugins
- Custom rule definitions

### Key Milestones Achieved

#### ✅ Milestone 1: Parser Ready
- Git diff extraction working
- Python AST parser handles common patterns
- Extended to JavaScript, TypeScript, Go, Java

#### ✅ Milestone 2: Agents Ready
- All 3 agents connected to free APIs (Gemini, Groq with 2 models)
- Consensus scoring working
- SQL Injection, XSS, Command Injection detection working

#### ✅ Milestone 3: MVP Complete
- Pre-commit hook integrated
- Ignore file, baseline mode working
- Terminal UI complete
- JSON output working

#### ✅ Milestone 4: Enhanced Features
- Cross-file taint analysis
- Attack chain visualization
- Multi-language support
- Call graph analysis

---

## Project Structure

```
security-audit-pipeline/
├── security_audit.py           # CLI entry point with argument parsing
├── orchestrator.py             # Main pipeline orchestrator
├── agents/
│   ├── code_parser.py          # Stage 1: AST parsing
│   ├── security_agents.py      # Stage 2: Multi-agent analysis (Gemini, Groq, HF)
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
├── tests/                      # Test suite
│   ├── test_ignore_filter.py
│   ├── test_baseline_manager.py
│   ├── test_config_manager.py
│   └── test_integration.py
├── requirements.txt            # Python dependencies
├── .env.example                # API key template
├── .pre-commit-hooks.yaml      # Pre-commit hook config
├── .secaudit.yaml              # File filter config
└── README.md                   # Public documentation
```

---

## Dependencies & Setup

### Python Requirements

```
python>=3.8
google-generativeai>=0.3.0          # Gemini API
groq>=0.4.0                         # Groq API
# Removed: huggingface-hub (replaced with Groq Llama 3.3 70B)
PyYAML>=6.0                         # Config files
rich>=13.0.0                        # Terminal UI
GitPython>=3.1.0                    # Git operations
```

### API Keys Required

```bash
# .env file
GEMINI_API_KEY=your_gemini_key_here
GROQ_API_KEY=your_groq_key_here
# Removed: HUGGINGFACE_API_KEY (no longer needed)
```

### Installation

```bash
# Clone and install
git clone https://github.com/yourusername/security-audit-pipeline.git
cd security-audit-pipeline

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure API keys
cp .env.example .env
# Edit .env with your API keys

# Install pre-commit hook
pre-commit install
```

---

## Known Limitations (Current Implementation)

1. **API Rate Limits** - All agents use free-tier APIs
   - Gemini: 15 RPM (sufficient for most use cases)
   - Groq: 14,400 requests/day per model (very generous)
   - Typical usage (10-50 commits/day) stays well within limits

2. **Multi-Language Support** - Python, JavaScript, TypeScript, Go, Java supported
   - Additional languages can be added via ParserFactory pattern

3. **Cross-File Analysis** - Implemented for taint tracking and attack chains
   - Requires full codebase context for best results

4. **Model Diversity** - Two agents use Groq (different models)
   - Different model sizes (8B vs 70B) provide diverse reasoning
   - Combined with Gemini for strong 3-perspective consensus

---

## Success Criteria for MVP

- [x] All 3 agents integrated and responding correctly (Gemini, Groq Llama 3.1 8B, Groq Llama 3.3 70B)
- [x] 2/3 consensus threshold working
- [x] <30s execution on vulnerable code
- [x] <10% false positive rate on test suite
- [x] Pre-commit hook blocks critical vulnerabilities
- [x] Baseline mode enables adoption on existing codebases
- [x] Terminal UI shows clear, actionable findings
- [x] JSON output compatible with CI/CD pipelines
- [x] <5 minute setup from install to first scan
- [x] Documentation complete and tested

**Status:** ✅ All MVP success criteria met

---

## Appendix: Comparison with Existing Tools

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
| **Free tier** | Unlimited* | ✅ | 10 scans/mo | 200 tests/mo |
| **Pre-commit hook** | ✅ | ✅ | ✅ | ❌ |
| **Token cost per commit** | 0.6K (~$0.0001) | N/A | N/A | N/A |
| **Languages** | Python (MVP) | Python | 30+ | 30+ |
| **Setup time** | 5 minutes | 2 minutes | 5 minutes | 10 minutes |

*Free tier: Groq provides 14,400 requests/day per model. With 2 models (8B + 70B), that's ~7,200 commits/day capacity.*

---

## FAQ

**Q: Why use two different Groq models instead of three different providers?**  
A: Groq's free tier is extremely generous and fast. Using Llama 3.1 8B (fast, adversarial) and Llama 3.3 70B (thorough, defensive) gives us model diversity without additional API keys or costs. Different model sizes provide genuinely different reasoning patterns.

**Q: What if I hit Groq API rate limits?**  
A: Groq's free tier is very generous (14,400 requests/day for Llama 3.1, 14,400 for Llama 3.3). For typical usage (10-50 commits/day), you won't hit limits. If you do, the pipeline will notify you.

**Q: Does using the same provider for two agents reduce accuracy?**  
A: No. Testing shows that model size diversity (8B vs 70B) provides different reasoning depths. Combined with Gemini's different architecture, we get strong 3-perspective consensus.

**Q: Can I use this in CI/CD?**  
A: Yes. Use `--json` for structured output and `--fail-on-high` or `--strict` for exit code control.

**Q: How do I exclude test files?**  
A: Create `.secaudit.yaml` with exclude patterns. Test files, migrations, and common patterns are excluded by default.

**Q: What if I disagree with a finding?**  
A: Add it to `.secaudit-ignore` file. Format: `filepath:line:VULN_TYPE`. The vulnerability will be filtered out on future runs.

**Q: Can I adopt this on an existing codebase?**  
A: Yes! Use `--baseline` mode. First run creates a baseline, subsequent runs only show NEW vulnerabilities. Adopt incrementally without fixing everything first.

---

## Contact & Support

- **GitHub Issues:** [Project Issues]
- **Discussions:** [Project Discussions]
- **Email:** support@example.com

---

**Last Updated:** April 30, 2025  
**Status:** MVP Complete - All free-tier APIs (Gemini + Groq dual-model)  
**Next Review:** When starting Phase 3 (Auto-fix & IDE plugins)
