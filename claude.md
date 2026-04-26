# Security Audit Pipeline — Configuration
_Last updated: 2026-04-26_

## Pipeline Settings
- Consensus threshold: 2/3 agents must agree
- Critical vulnerabilities: require all 3 agents for high confidence
- Pre-commit hook: blocks commits with CRITICAL or HIGH severity vulns

## API Configuration
- Gemini: gemini-2.5-flash-lite (higher rate limits)
- Groq: llama-3.1-8b-instant (higher rate limits)
- Claude: Agent C uses heuristic analysis (no API key needed)

## Rate Limit Strategy
- Gemini free tier: 1500 RPD
- Groq free tier: generous limits
- Graceful degradation: runs with 2-agent consensus if one API fails

## Session Notes
(Auto-populated during development)

---
### 2026-04-26 - Initial Setup
Project initialized with 5-stage security audit pipeline architecture.

