# API Resilience & Graceful Degradation

## Overview

The security audit pipeline now includes robust retry logic and graceful degradation to handle API failures, rate limits, and network issues.

## Features

### 1. Automatic Retry with Exponential Backoff

All three agents (A, B, C) automatically retry failed API calls:

- **Max attempts**: 3 retries per agent
- **Backoff strategy**: Exponential (2s, 4s, 8s)
- **Retry triggers**: Any API error (rate limits, timeouts, network issues)

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((Exception,)),
    reraise=True
)
def agent_a_static_analysis(self, extraction):
    # Agent logic with automatic retry
```

### 2. Graceful Degradation

The system continues operating even when agents fail:

- **3 agents active**: Requires 2/3 consensus (66%)
- **2 agents active**: Requires 2/2 consensus (100%)
- **1 agent active**: Insufficient for consensus (skips file)

Example output:
```
✗ Agent A failed after 3 retries
⚠ Running with 2/3 agents (degraded mode)
⚠ Failed: Agent A
```

### 3. Multi-Model Fallback (Agent A)

Agent A (Gemini) tries multiple models before failing:

1. `gemini-2.0-flash` (primary)
2. `gemini-1.5-flash` (fallback)
3. `gemini-1.5-flash-8b` (last resort)

If rate limited on one model, automatically tries the next.

### 4. Comprehensive Logging

All failures are logged for debugging:

```python
logger.error(f"Agent A failed: {error_message}")
logger.info(f"Agent B completed successfully")
```

Logs include:
- Which agent failed
- Error details
- Retry attempts
- Degraded mode status

## SaaS-Ready Improvements

### Before (MVP)
- ❌ Single API failure = entire pipeline fails
- ❌ No retry logic
- ❌ Silent failures
- ❌ No degraded mode

### After (Production-Ready)
- ✅ Continues with 2/3 agents if one fails
- ✅ 3 automatic retries with exponential backoff
- ✅ Clear error messages and logging
- ✅ Graceful degradation with consensus adjustment

## Testing

### Simulating API Failures

```bash
# Test with rate-limited API
export GEMINI_API_KEY="invalid_key"
python3 security_audit.py

# Expected: Agent A fails, continues with Agents B & C
```

### Monitoring Degraded Mode

Check logs for:
- `⚠ Running with 2/3 agents (degraded mode)`
- `✗ Agent X failed after 3 retries`
- `ERROR:agents.security_agents:Agent X failed: ...`

## Performance Impact

- **Normal operation**: No performance impact
- **Single retry**: +2-4 seconds per agent
- **Full retries (3x)**: +14 seconds max per agent
- **Degraded mode (2 agents)**: ~33% faster than 3 agents

## Next Steps for Production

1. **Paid API Tiers**: Switch to paid Gemini Pro and Groq paid for higher rate limits
2. **Queue System**: Add job queue for when all agents are down
3. **Health Checks**: Endpoint to monitor agent availability
4. **Metrics**: Track failure rates, retry counts, degraded mode frequency
5. **Alerting**: Notify when running in degraded mode for extended periods

## Configuration

Add to `.env`:
```bash
# Retry configuration (optional)
MAX_RETRIES=3
RETRY_MIN_WAIT=2
RETRY_MAX_WAIT=10

# Consensus configuration
MIN_AGENTS_FOR_CONSENSUS=2
```

## Dependencies

```bash
pip install tenacity>=8.0.0
```

The `tenacity` library provides the retry logic with exponential backoff.
