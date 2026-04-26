# Security Audit Pipeline - Usage Guide

## Quick Start

### Run Security Audit

```bash
cd /Users/mohitsahoo/Desktop/Aiagents/security-audit-pipeline

# Run on staged files (default)
python security_audit.py

# Run on specific file
python security_audit.py --file path/to/file.py

# Force re-run (ignore cache)
python security_audit.py --force
```

## Outputs

After running the pipeline, check `cache/` directory:

### 1. Stage 1: Code Parsing (`stage1_parsed.json`)

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

### 2. Stage 2: Multi-Agent Analysis (`stage2_consensus.json`)

Findings from 3 security agents:

```bash
# View consensus findings
cat cache/stage2_consensus.json | jq '.consensus_findings[]'

# View high confidence vulnerabilities
cat cache/stage2_consensus.json | jq '.consensus_findings[] | select(.confidence=="HIGH")'

# Count findings by type
cat cache/stage2_consensus.json | jq '.consensus_findings | group_by(.type) | map({type: .[0].type, count: length})'
```

**Structure:**
- `agent_a_findings[]`: Static analysis (Gemini) - OWASP patterns
- `agent_b_findings[]`: Adversarial attacker (Groq) - exploitation perspective
- `agent_c_findings[]`: Defensive architect (Claude) - blast radius
- `consensus_findings[]`: 2/3 agreement threshold
  - `type`: SQL_INJECTION, XSS, COMMAND_INJECTION, etc.
  - `location`: File path and line number
  - `confidence`: HIGH (3/3) or MEDIUM (2/3)
  - `evidence`: Code snippet showing vulnerability

### 3. Stage 3: Severity Debate (`stage3_debate.json`)

Severity classification after debate:

```bash
# View final severity rankings
cat cache/stage3_debate.json | jq '.final_rankings[]'

# View debate reasoning
cat cache/stage3_debate.json | jq '.debate_summary'
```

**Structure:**
- `final_rankings[]`: Vulnerabilities with adjusted severity
  - `type`: Vulnerability type
  - `original_severity`: Before debate
  - `final_severity`: After debate (CRITICAL/HIGH/MEDIUM/LOW)
  - `reasoning`: Why severity was adjusted
- `debate_summary`: Key points from severity discussion

### 4. Stage 4: Verification (`stage4_verified.json`)

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
  - `vuln_type`: Vulnerability type
  - `cwe_id`: CWE identifier (e.g., "CWE-89")
  - `description`: CWE description
  - `severity`: CRITICAL/HIGH/MEDIUM/LOW
- `attack_trees[]`: Attack path visualization
  - `root`: Attack goal
  - `steps[]`: Exploitation steps
  - `difficulty`: EASY/MEDIUM/HARD
  - `time_estimate`: Time to exploit
- `mitigations[]`: Fix recommendations
  - `vuln_type`: Vulnerability type
  - `recommendation`: How to fix
  - `code_example`: Secure code pattern

## Terminal Output

When running the pipeline, you'll see:

1. **Stage Progress**
   - Stage 1: Parsing Python code...
   - Stage 2: Multi-agent analysis...
   - Stage 3: Severity debate...
   - Stage 4: CWE verification...
   - Stage 5: Generating report...

2. **Vulnerability Summary**
   - Total vulnerabilities found
   - Critical/High/Medium/Low counts
   - Exit code (0=clean, 1=block, 2=error)

3. **Detailed Findings**
   - Vulnerability type
   - Location (file:line)
   - Severity + confidence
   - CWE ID
   - Evidence (code snippet)

4. **Attack Trees**
   - Visual tree showing exploitation paths
   - Difficulty and time estimates
   - Step-by-step attack flow

## Verification

Run verification script to check implementation:

```bash
python verify_implementation.py
```

This checks:
- All 5 stages complete successfully
- Cache files exist and are valid JSON
- Consensus threshold working (2/3 agents)
- Attack trees generated
- Terminal report renders correctly

## Examples

### Example 1: View Consensus Findings

```bash
# Count vulnerabilities by confidence
jq '[.consensus_findings[] | .confidence] | group_by(.) | map({confidence: .[0], count: length})' cache/stage2_consensus.json

# List all SQL injection findings
jq '.consensus_findings[] | select(.type=="SQL_INJECTION")' cache/stage2_consensus.json
```

### Example 2: Explore Attack Trees

```bash
# View all attack goals
jq -r '.attack_trees[] | .root' cache/stage4_verified.json

# View steps for first attack tree
jq '.attack_trees[0].steps[]' cache/stage4_verified.json
```

### Example 3: Check CWE Mappings

```bash
# List all CWE IDs found
jq -r '.cwe_mappings[] | .cwe_id' cache/stage4_verified.json | sort -u

# View critical severity CWEs
jq '.cwe_mappings[] | select(.severity=="CRITICAL")' cache/stage4_verified.json
```

## Troubleshooting

### Missing Outputs

If some cache files are missing:

```bash
# Check which stages completed
ls -la cache/

# Re-run with force flag
python security_audit.py --force
```

### No Vulnerabilities Detected

If audit finds nothing but you expect vulnerabilities:

```bash
# Check if code patterns are recognized
cat cache/stage1_parsed.json | jq '.sql_patterns, .user_inputs, .subprocess_calls'

# Lower consensus threshold (edit agents/security_agents.py)
# Change CONSENSUS_THRESHOLD from 2 to 1
```

### Agent Failures

If an agent fails:
- Tool gracefully degrades to 2-agent consensus
- Check API keys in `.env`
- Check network connectivity
- View error in terminal output

### False Positives

If audit flags safe code:
- Review evidence in terminal output
- Check if input validation exists but wasn't detected
- Add exception to `.security-audit-ignore` (future feature)

## Pre-Commit Hook Integration

### Install Hook

```bash
pre-commit install
```

### Test Hook

```bash
# Stage vulnerable code
git add test_vuln.py

# Try to commit (should be blocked)
git commit -m "test"
```

### Bypass Hook (Emergency Only)

```bash
# Skip security audit (NOT RECOMMENDED)
git commit --no-verify -m "emergency fix"
```

## Token Usage Tracking

View token usage:

```bash
# Check token tracker output
cat cache/token_usage.json | jq '.'

# View usage by agent
cat cache/token_usage.json | jq '.by_agent'

# View total tokens
cat cache/token_usage.json | jq '.total'
```

## Next Steps

1. **Run on real codebase:** Test with actual Python projects
2. **Review findings:** Check terminal output for vulnerabilities
3. **Fix issues:** Apply mitigation advice
4. **Re-run:** Verify fixes pass audit
5. **Integrate:** Add to CI/CD pipeline

## Advanced Usage

### Custom CWE Database

Edit `tools/cwe_database.py` to add custom vulnerability patterns:

```python
CUSTOM_PATTERNS = {
    "MY_VULN_TYPE": {
        "cwe_id": "CWE-XXX",
        "description": "Custom vulnerability description",
        "severity": "HIGH",
        "mitigation": "How to fix it"
    }
}
```

### Adjust Consensus Threshold

Edit `agents/security_agents.py`:

```python
# Stricter (require all 3 agents)
CONSENSUS_THRESHOLD = 3

# More lenient (require only 1 agent)
CONSENSUS_THRESHOLD = 1
```

### Custom Agent Prompts

Edit agent prompts in:
- `agents/security_agents.py` - Multi-agent analysis prompts
- `agents/debate_room.py` - Severity debate prompts
- `agents/verifier.py` - Verification prompts

## Performance Optimization

### Skip Clean Files

Pipeline automatically skips files with no security-relevant patterns (SQL, user inputs, subprocess calls, file operations).

### Cache Results

Pipeline caches results per file. Re-running on unchanged files uses cache.

### Parallel Execution (Future)

Currently sequential. Future: parallel agent execution for faster analysis.

## Integration with CI/CD

### GitHub Actions

```yaml
- name: Security Audit
  run: |
    pip install -r requirements.txt
    python security_audit.py
```

### GitLab CI

```yaml
security_audit:
  script:
    - pip install -r requirements.txt
    - python security_audit.py
```

### Pre-Push Hook

```bash
# .git/hooks/pre-push
#!/bin/bash
python security_audit.py
```
