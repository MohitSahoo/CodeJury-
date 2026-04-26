"""Stage 2: Multi-agent research with consensus scoring."""

import os
import json
import time
from pathlib import Path
from typing import Dict, Any, List
import google.generativeai as genai
from groq import Groq
from rich.console import Console

console = Console()


class ResearchAgent:
    """Run 3 research agents with different perspectives."""

    def __init__(self, gemini_key: str = None, groq_key: str = None):
        """Initialize research agents."""
        self.gemini_key = gemini_key or os.getenv("GEMINI_API_KEY")
        self.groq_key = groq_key or os.getenv("GROQ_API_KEY")

        if not self.gemini_key:
            raise ValueError("GEMINI_API_KEY not found")
        if not self.groq_key:
            raise ValueError("GROQ_API_KEY not found")

        # Configure APIs
        genai.configure(api_key=self.gemini_key)
        self.gemini_model = genai.GenerativeModel("gemini-2.5-flash")
        self.groq_client = Groq(api_key=self.groq_key)

    def research(self, extraction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run all 3 research agents.

        Args:
            extraction: Stage 1 extraction output

        Returns:
            Dict with outputs from all 3 agents
        """
        console.print("\n[bold cyan]Running research agents...[/bold cyan]\n")

        # Agent A: Gemini (neutral extractor)
        console.print("[bold]Agent A: Gemini (Neutral Technical Extractor)[/bold]")
        gemini_output = self._run_agent_a(extraction)
        self._save_output("cache/stage2_gemini.json", gemini_output)
        time.sleep(4)  # 15 RPM limit

        # Agent B: Groq (skeptical engineer)
        groq_output = None
        console.print("\n[bold]Agent B: Groq (Skeptical Engineer)[/bold]")
        try:
            groq_output = self._run_agent_b(extraction)
            self._save_output("cache/stage2_groq.json", groq_output)
            time.sleep(1)  # Groq is fast, minimal rate limit
        except Exception as e:
            console.print(f"  [yellow]⚠ Groq unavailable: {str(e)[:100]}[/yellow]")
            console.print("  [yellow]Continuing with 2-agent consensus[/yellow]")
            groq_output = {"error": "quota_exceeded", "gaps": [], "concerns": []}
            self._save_output("cache/stage2_groq.json", groq_output)

        # Agent C: Claude (practical educator)
        console.print("\n[bold]Agent C: Claude (Practical Educator)[/bold]")
        claude_output = self._run_agent_c(extraction)
        self._save_output("cache/stage2_claude.json", claude_output)

        console.print("\n[green]✓ Research complete[/green]")

        return {
            "gemini": gemini_output,
            "groq": groq_output,
            "claude": claude_output,
        }

    def _run_agent_a(self, extraction: Dict[str, Any]) -> Dict[str, Any]:
        """Agent A: Gemini neutral technical extractor."""
        prompt = f"""You are a neutral technical analyst. Review this tutorial extraction and identify technical claims with evidence.

Tutorial: {extraction['title']}
Summary: {extraction['summary']}
Steps: {json.dumps(extraction['steps'], indent=2)}
Code: {json.dumps(extraction['code_shown'], indent=2)}
Tools: {extraction['tools_used']}
Concepts: {extraction['key_concepts']}

Extract atomic technical claims with timestamp evidence. Return JSON:
{{
  "claims": [
    {{
      "claim": "specific technical statement",
      "evidence": "timestamp or code reference",
      "confidence": "high|medium|low"
    }}
  ],
  "technical_accuracy_notes": "any concerns about accuracy"
}}"""

        response = self.gemini_model.generate_content(prompt)
        return self._parse_json_response(response.text)

    def _run_agent_b(self, extraction: Dict[str, Any]) -> Dict[str, Any]:
        """Agent B: Groq skeptical engineer."""
        prompt = f"""You are a skeptical senior engineer reviewing a tutorial. Find gaps, assumptions, and potential errors.

Tutorial: {extraction['title']}
Summary: {extraction['summary']}
Steps: {json.dumps(extraction['steps'], indent=2)}
Code: {json.dumps(extraction['code_shown'], indent=2)}
Tools: {extraction['tools_used']}
Prerequisites: {extraction['prerequisites']}

Identify:
1. Missing error handling or edge cases
2. Unstated assumptions
3. Potential security issues
4. Oversimplifications
5. Missing prerequisites

Return JSON:
{{
  "gaps": ["gap 1", "gap 2"],
  "assumptions": ["assumption 1", "assumption 2"],
  "concerns": ["concern 1", "concern 2"],
  "missing_context": ["context 1", "context 2"]
}}"""

        response = self.groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
        )

        return self._parse_json_response(response.choices[0].message.content)

    def _run_agent_c(self, extraction: Dict[str, Any]) -> Dict[str, Any]:
        """Agent C: Claude practical educator (prompt-based)."""
        # This returns a structured prompt for Claude to process
        # In actual implementation, this would be a Claude API call
        # For now, return a structured analysis prompt
        return {
            "role": "practical_educator",
            "focus": "beginner_confusion_points",
            "analysis_prompt": f"""You are a practical educator. Review this tutorial for beginner confusion points.

Tutorial: {extraction['title']}
Summary: {extraction['summary']}
Steps: {json.dumps(extraction['steps'], indent=2)}
Prerequisites: {extraction['prerequisites']}
Key Concepts: {extraction['key_concepts']}

Identify:
1. Concepts that need more explanation
2. Steps that might confuse beginners
3. Missing "why" explanations
4. Jargon that needs definition

Return JSON:
{{
  "confusing_concepts": ["concept 1", "concept 2"],
  "unclear_steps": ["step description"],
  "missing_explanations": ["what needs explaining"],
  "jargon_to_define": ["term 1", "term 2"]
}}""",
            "note": "This is a prompt template. In production, call Claude API here.",
        }

    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """Parse JSON from API response, handling markdown fences."""
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1])
            if text.startswith("json"):
                text = text[4:].strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Return raw text if not valid JSON
            return {"raw_response": text, "parse_error": True}

    def _save_output(self, path: str, data: Dict[str, Any]) -> None:
        """Save agent output to cache."""
        Path(path).parent.mkdir(exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        console.print(f"  ✓ Saved to {path}", style="green")


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

    # Load Stage 1 extraction
    with open("cache/stage1_extraction.json") as f:
        extraction = json.load(f)

    # Run research
    agent = ResearchAgent()
    results = agent.research(extraction)

    print("\n" + "=" * 60)
    print("RESEARCH COMPLETE")
    print("=" * 60)
