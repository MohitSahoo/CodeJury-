"""
Stage 2: Multi-Agent Security Analysis
Three security agents analyze code from different perspectives.
"""

import os
import json
import time
import logging
from typing import Dict, List, Any
from pathlib import Path

from google import genai
from groq import Groq
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    RetryError
)

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SecurityAgents:
    """Three security agents with different perspectives."""

    def __init__(self):
        """Initialize API clients."""
        # Gemini setup (optional - will skip Agent A if unavailable)
        gemini_key = os.getenv('GEMINI_API_KEY')
        if gemini_key:
            try:
                self.gemini_client = genai.Client(api_key=gemini_key)
            except Exception as e:
                print(f"Warning: Failed to initialize Gemini client: {e}")
                self.gemini_client = None
        else:
            print("Warning: GEMINI_API_KEY not found - Agent A will be skipped")
            self.gemini_client = None

        # Groq setup (required - used for both Agent B and Agent C)
        groq_key = os.getenv('GROQ_API_KEY')
        if not groq_key:
            raise ValueError("GROQ_API_KEY not found in .env - at least one API key is required")
        self.groq = Groq(api_key=groq_key)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True
    )
    def agent_a_static_analysis(self, extraction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Agent A: Static analysis perspective (Gemini with Fallback).
        """
        print("  Agent A (Static Analysis - Gemini)...")

        prompt = f"""You are a static analysis security tool analyzing code.
Analyze this code extraction for vulnerabilities (SQL Injection, XSS, Command Injection, etc.).

Code extraction:
{json.dumps(extraction, indent=2)}

Return ONLY valid JSON:
{{
  "vulnerabilities": [
    {{
      "type": "VULN_TYPE",
      "location": "filename:lineno",
      "severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "confidence": "HIGH|MEDIUM|LOW",
      "description": "...",
      "evidence": "...",
      "cwe_id": "CWE-XX"
    }}
  ]
}}
"""
        # Model fallback chain for resilience
        models_to_try = [
            'gemini-2.0-flash',
            'gemini-1.5-flash',
            'gemini-1.5-flash-8b'
        ]

        last_error = None
        for model_name in models_to_try:
            try:
                if not self.gemini_client:
                    break

                response = self.gemini_client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                result_text = response.text.strip() if response.text else ""

                if not result_text:
                    raise ValueError("Empty response from Gemini")

                # Clean markdown fences
                if result_text.startswith('```'):
                    result_text = result_text.split('```')[1]
                    if result_text.startswith('json'):
                        result_text = result_text[4:]
                    result_text = result_text.strip()

                result = json.loads(result_text)
                print(f"    ✓ Found {len(result.get('vulnerabilities', []))} vulnerabilities (using {model_name})")
                return result

            except Exception as e:
                last_error = str(e)
                if "429" in last_error or "RESOURCE_EXHAUSTED" in last_error:
                    print(f"    ⚠ {model_name} rate limited, trying fallback...")
                    time.sleep(1) # Small pause before retry
                    continue
                else:
                    print(f"    ✗ {model_name} error: {e}")
                    break

        # All models failed - raise exception for retry logic
        error_msg = f"All Gemini models failed: {last_error}"
        logger.error(error_msg)
        raise Exception(error_msg)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True
    )
    def agent_b_adversarial(self, extraction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Agent B: Adversarial attacker perspective (Groq).
        Thinks like a penetration tester trying to exploit the code.
        """
        print("  Agent B (Adversarial Attacker - Groq)...")

        prompt = f"""You are a penetration tester analyzing Python code for exploitable vulnerabilities.

Code extraction:
{json.dumps(extraction, indent=2)}

Think like an attacker:
- What's the easiest way to compromise this code?
- Can I bypass authentication or authorization?
- Can I inject malicious input to execute arbitrary code?
- Can I access files or data I shouldn't?
- What's the blast radius if I exploit this?

For each exploitable vulnerability, return JSON:
{{
  "vulnerabilities": [
    {{
      "type": "SQL_INJECTION|XSS|PATH_TRAVERSAL|COMMAND_INJECTION|etc",
      "location": "filename:lineno",
      "severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "confidence": "HIGH|MEDIUM|LOW",
      "description": "How an attacker would exploit this",
      "evidence": "Code snippet",
      "cwe_id": "CWE-XX",
      "exploit_difficulty": "EASY|MEDIUM|HARD",
      "blast_radius": "Brief description of impact"
    }}
  ]
}}

Return ONLY valid JSON, no markdown."""

        try:
            response = self.groq.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6,
                max_tokens=2000
            )

            result_text = response.choices[0].message.content
            if not result_text:
                raise ValueError("Empty response from Groq")

            result_text = result_text.strip()

            # Clean markdown fences
            if result_text.startswith('```'):
                result_text = result_text.split('```')[1]
                if result_text.startswith('json'):
                    result_text = result_text[4:]
                result_text = result_text.strip()

            result = json.loads(result_text)
            print(f"    ✓ Found {len(result.get('vulnerabilities', []))} vulnerabilities")
            return result

        except json.JSONDecodeError as e:
            error_msg = f"JSON parse error: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            logger.error(f"Agent B error: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True
    )
    def agent_c_groq(self, extraction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Agent C: Defensive architect perspective (Groq with different model).
        Focuses on blast radius, impact assessment, and defense-in-depth.
        Uses a different Groq model than Agent B for diverse perspective.
        """
        print("  Agent C (Defensive Architect - Groq Llama)...")

        prompt = f"""You are a defensive security architect analyzing Python code.
Focus on blast radius, impact assessment, and missing security controls.

Code extraction:
{json.dumps(extraction, indent=2)}

Analyze from a defensive perspective:
- What is the worst-case impact if this code is exploited?
- What security controls are missing?
- What is the blast radius of each vulnerability?
- Are there defense-in-depth failures?

For each vulnerability found, return JSON:
{{
  "vulnerabilities": [
    {{
      "type": "SQL_INJECTION|XSS|PATH_TRAVERSAL|COMMAND_INJECTION|etc",
      "location": "filename:lineno",
      "severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "confidence": "HIGH|MEDIUM|LOW",
      "description": "Brief description focusing on impact and blast radius",
      "evidence": "Code snippet",
      "cwe_id": "CWE-XX"
    }}
  ]
}}

Return ONLY valid JSON, no markdown, no explanations."""

        try:
            # Use different model than Agent B for diverse perspective
            response = self.groq.chat.completions.create(
                model="llama-3.3-70b-versatile",  # Different from Agent B's llama-3.1-8b
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,  # Slightly higher for more creative defensive thinking
                max_tokens=2000
            )

            result_text = response.choices[0].message.content
            if not result_text:
                raise ValueError("Empty response from Groq")

            result_text = result_text.strip()

            # Clean markdown fences
            if result_text.startswith('```'):
                result_text = result_text.split('```')[1]
                if result_text.startswith('json'):
                    result_text = result_text[4:]
                result_text = result_text.strip()

            result = json.loads(result_text)
            print(f"    ✓ Found {len(result.get('vulnerabilities', []))} vulnerabilities")
            return result

        except json.JSONDecodeError as e:
            error_msg = f"JSON parse error: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            logger.error(f"Agent C error: {e}")
            raise

    def agent_c_manual(self, extraction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Agent C: Generate a prompt for the user to paste into Claude Code.
        """
        print("\n" + "="*80)
        print("🤖 CLAUDE CODE MODE: Agent C (Defensive Architect)")
        print("="*80)
        print(f"\nPlease copy the prompt below and paste it into your Claude Code terminal.")
        print(f"When Claude responds with JSON, paste the JSON back here and press ENTER.\n")
        
        prompt = f"""You are a Defensive Security Architect. Analyze this code extraction for vulnerabilities.
Focus on defense-in-depth, blast radius, and missing security controls.

Code extraction:
{json.dumps(extraction, indent=2)}

For each vulnerability found, return ONLY a JSON object:
{{
  "vulnerabilities": [
    {{
      "type": "SQL_INJECTION|XSS|PATH_TRAVERSAL|COMMAND_INJECTION|etc",
      "location": "filename:lineno",
      "severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "confidence": "HIGH|MEDIUM|LOW",
      "description": "Brief description",
      "evidence": "Code snippet",
      "cwe_id": "CWE-XX"
    }}
  ]
}}
"""
        print("-" * 40 + " COPY FROM HERE " + "-" * 40)
        print(prompt)
        print("-" * 40 + " END OF PROMPT " + "-" * 40)
        
        print("\nWaiting for Claude's JSON response (paste below and press ENTER):")
        
        # Read lines until we have a valid JSON block
        lines = []
        while True:
            try:
                line = input()
                if not line and lines: # Stop on empty line if we have content
                    break
                lines.append(line)
                # Check if it's already valid JSON
                content = "\n".join(lines).strip()
                if content.startswith('{') and content.endswith('}'):
                    try:
                        json.loads(content)
                        break
                    except:
                        pass
            except EOFError:
                break
        
        content = "\n".join(lines).strip()
        # Clean markdown fences if present
        if "```" in content:
            parts = content.split("```")
            for part in parts:
                part = part.strip()
                if part.startswith("json"):
                    part = part[4:].strip()
                if part.startswith("{") and part.endswith("}"):
                    content = part
                    break
        
        try:
            result = json.loads(content)
            print(f"    ✓ Received {len(result.get('vulnerabilities', []))} vulnerabilities from Claude Code")
            return result
        except Exception as e:
            print(f"    ✗ Error parsing Claude Code response: {e}")
            return {"vulnerabilities": []}

    def agent_c_defensive(self, extraction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Agent C: Defensive architect perspective (Claude prompt template).
        Focuses on defense-in-depth failures and missing security controls.

        Note: This returns a prompt template for Claude Code to execute.
        In production, this would call Claude API directly.
        """
        print("  Agent C (Defensive Architect - Claude)...")

        # For MVP, we'll use a simplified heuristic-based approach
        # In production, this would call Claude API
        vulnerabilities = []

        # Check for SQL injection patterns
        if extraction.get('sql_patterns'):
            for sql in extraction['sql_patterns']:
                if sql.get('uses_formatting') or sql.get('risk') == 'HIGH':
                    vulnerabilities.append({
                        "type": "SQL_INJECTION",
                        "location": f"{extraction['filepath']}:{sql['lineno']}",
                        "severity": "CRITICAL",
                        "confidence": "HIGH",
                        "description": "SQL query uses string formatting with potential user input - vulnerable to SQL injection",
                        "evidence": sql['query_snippet'],
                        "cwe_id": "CWE-89"
                    })

        # Check for missing input validation
        if extraction.get('user_inputs'):
            for inp in extraction['user_inputs']:
                vulnerabilities.append({
                    "type": "MISSING_INPUT_VALIDATION",
                    "location": f"{extraction['filepath']}:{inp['lineno']}",
                    "severity": "MEDIUM",
                    "confidence": "MEDIUM",
                    "description": f"User input from {inp['source']} lacks validation",
                    "evidence": inp['source'],
                    "cwe_id": "CWE-20"
                })

        # Check for path traversal in file operations
        if extraction.get('file_operations'):
            for op in extraction['file_operations']:
                if op.get('has_user_input') or op.get('risk') == 'HIGH':
                    vulnerabilities.append({
                        "type": "PATH_TRAVERSAL",
                        "location": f"{extraction['filepath']}:{op['lineno']}",
                        "severity": "HIGH",
                        "confidence": "HIGH",
                        "description": f"File operation {op['operation']} uses user input without path validation",
                        "evidence": op['operation'],
                        "cwe_id": "CWE-22"
                    })

        # Check for command injection
        if extraction.get('subprocess_calls'):
            for call in extraction['subprocess_calls']:
                if call['risk'] in ['CRITICAL', 'HIGH']:
                    vulnerabilities.append({
                        "type": "COMMAND_INJECTION",
                        "location": f"{extraction['filepath']}:{call['lineno']}",
                        "severity": "CRITICAL" if call['risk'] == 'CRITICAL' else "HIGH",
                        "confidence": "HIGH",
                        "description": f"Subprocess call {call['function']} with user input and/or shell=True",
                        "evidence": call['function'],
                        "cwe_id": "CWE-78"
                    })

        # Check for insecure deserialization (pickle.loads with tainted data)
        if extraction.get('dangerous_imports'):
            has_pickle = any(imp['module'] == 'pickle' for imp in extraction['dangerous_imports'])
            if has_pickle and extraction.get('tainted_variables'):
                # Flag as potential insecure deserialization
                vulnerabilities.append({
                    "type": "INSECURE_DESERIALIZATION",
                    "location": f"{extraction['filepath']}:1",
                    "severity": "CRITICAL",
                    "confidence": "MEDIUM",
                    "description": "pickle module imported with user input present - potential insecure deserialization",
                    "evidence": "pickle + tainted variables",
                    "cwe_id": "CWE-502"
                })

        # Check for XSS (HTML output with user input)
        if extraction.get('user_inputs') and extraction.get('tainted_variables'):
            # Look for HTML-like patterns in string formatting
            for fmt in extraction.get('string_formatting', []):
                vulnerabilities.append({
                    "type": "XSS",
                    "location": f"{extraction['filepath']}:{fmt['lineno']}",
                    "severity": "HIGH",
                    "confidence": "MEDIUM",
                    "description": "String formatting with user input may produce unescaped HTML output",
                    "evidence": fmt['type'],
                "cwe_id": "CWE-79"
                })

        print(f"    ✓ Found {len(vulnerabilities)} vulnerabilities")

        return {"vulnerabilities": vulnerabilities}


def run_stage2(extractions: List[Dict[str, Any]], config: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """
    Stage 2: Multi-agent security analysis (Parallel Edition).
    """
    if config is None:
        config = {}

    # Check cache first
    cache_file = Path('cache/stage2_consensus.json')
    if cache_file.exists():
        print("✓ Stage 2 cache found, loading...")
        with open(cache_file) as f:
            return json.load(f)

    print("\nStage 2: Multi-Agent Security Analysis (Parallel)")
    print("=" * 50)

    agents = SecurityAgents()
    all_results = []
    
    use_claude_code = config.get('claude_code', False)

    for extraction in extractions:
        filepath = extraction['filepath']
        if not extraction.get('has_security_patterns', True):
            print(f"\nSkipping {filepath} (no security patterns)")
            continue

        print(f"\nAnalyzing: {filepath}")

        # Parallel Execution of Agents with Graceful Degradation
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_agent = {}

            # Agent A (Gemini)
            if agents.gemini_client:
                future_to_agent[executor.submit(agents.agent_a_static_analysis, extraction)] = "Agent A"

            # Agent B (Groq 8B)
            future_to_agent[executor.submit(agents.agent_b_adversarial, extraction)] = "Agent B"

            # Agent C (Groq 70B or Manual)
            if use_claude_code:
                # Manual mode can't be fully parallel with others since it needs input
                # but we'll run A and B first, then C
                pass
            else:
                future_to_agent[executor.submit(agents.agent_c_groq, extraction)] = "Agent C"

            results = {}
            failed_agents = []

            for future in as_completed(future_to_agent):
                agent_name = future_to_agent[future]
                try:
                    result = future.result()
                    results[agent_name] = result
                    logger.info(f"{agent_name} completed successfully")
                except RetryError as e:
                    logger.error(f"{agent_name} failed after retries: {e}")
                    print(f"    ✗ {agent_name} failed after 3 retries")
                    failed_agents.append(agent_name)
                except Exception as e:
                    logger.error(f"{agent_name} failed: {e}")
                    print(f"    ✗ {agent_name} failed: {e}")
                    failed_agents.append(agent_name)

            # Handle Manual Agent C if needed
            if use_claude_code:
                try:
                    results["Agent C"] = agents.agent_c_manual(extraction)
                except Exception as e:
                    logger.error(f"Agent C (manual) failed: {e}")
                    print(f"    ✗ Agent C (manual) failed: {e}")
                    failed_agents.append("Agent C")

        # Graceful Degradation: Need at least 2 agents for consensus
        successful_agents = len(results)
        if successful_agents < 2:
            logger.error(f"Insufficient agents: only {successful_agents} succeeded, need at least 2")
            print(f"\n  ⚠ WARNING: Only {successful_agents} agent(s) succeeded")
            print(f"  ⚠ Failed agents: {', '.join(failed_agents)}")
            print(f"  ⚠ Need at least 2 agents for consensus - skipping this file")
            continue

        if failed_agents:
            print(f"  ⚠ Running with {successful_agents}/3 agents (degraded mode)")
            print(f"  ⚠ Failed: {', '.join(failed_agents)}")

        # Import consensus scorer
        from tools.security_consensus import score_security_consensus

        # Prepare results dict with empty defaults for missing agents
        results_dict = {
            "Agent A": {"vulnerabilities": []},
            "Agent B": {"vulnerabilities": []},
            "Agent C": {"vulnerabilities": []}
        }

        # Update with actual results
        for agent_name, result in results.items():
            results_dict[agent_name] = result

        # Score consensus (will handle missing agents)
        try:
            consensus = score_security_consensus(
                results_dict["Agent A"],
                results_dict["Agent B"],
                results_dict["Agent C"],
                extraction['filepath']
            )
        except ValueError as e:
            # Insufficient agents for consensus
            logger.error(f"Consensus failed: {e}")
            print(f"\n  ✗ {e}")
            continue

        all_results.append(consensus)

        print(f"\n  Consensus: {consensus['total_vulns']} vulnerabilities")
        print(f"    High confidence: {consensus['high_confidence']}")
        print(f"    Medium confidence: {consensus['medium_confidence']}")

    # Cache results
    cache_file.parent.mkdir(exist_ok=True)
    with open(cache_file, 'w') as f:
        json.dump(all_results, f, indent=2)

    print(f"\n✓ Stage 2 complete - cached to {cache_file}")
    return all_results


if __name__ == "__main__":
    # Test Stage 2
    from agents.code_parser import run_stage1

    print("Running Stage 1 first...")
    extractions = run_stage1()

    print("\nRunning Stage 2...")
    results = run_stage2(extractions)

    print(f"\n✓ Analyzed {len(results)} file(s)")
    total_vulns = sum(r['total_vulns'] for r in results)
    print(f"✓ Total vulnerabilities: {total_vulns}")
