"""Token usage tracking and warnings."""

import json
from typing import Dict, Any
from rich.console import Console

console = Console()


class TokenTracker:
    """Track token usage across API calls."""

    # Free tier limits
    GEMINI_DAILY_LIMIT = 1_000_000
    GROQ_DAILY_LIMIT = 14_400  # Free tier: 14.4K requests/day
    GROQ_COST_PER_1M = 0.0  # Free tier

    def __init__(self):
        self.usage = {
            "gemini": 0,
            "groq": 0,
            "claude": 0,
        }

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation: 1 token ≈ 4 chars)."""
        return len(text) // 4

    def log_stage(self, stage: str, provider: str, input_text: str, output_text: str = ""):
        """Log token usage for a stage."""
        input_tokens = self.estimate_tokens(input_text)
        output_tokens = self.estimate_tokens(output_text)
        total_tokens = input_tokens + output_tokens

        self.usage[provider] += total_tokens

        console.print(f"\n[dim]Token usage - {stage} ({provider}):[/dim]")
        console.print(f"  Input: ~{input_tokens:,} tokens")
        console.print(f"  Output: ~{output_tokens:,} tokens")
        console.print(f"  Total: ~{total_tokens:,} tokens")

        # Check warnings
        self._check_warnings(provider)

    def _check_warnings(self, provider: str):
        """Check if approaching limits."""
        if provider == "gemini":
            usage_pct = (self.usage["gemini"] / self.GEMINI_DAILY_LIMIT) * 100
            if usage_pct >= 80:
                console.print(
                    f"  [yellow]⚠ Warning: {usage_pct:.1f}% of Gemini daily limit used[/yellow]"
                )

        elif provider == "groq":
            # Groq free tier is request-based, not token-based
            # Just track tokens for visibility
            pass

    def get_summary(self) -> Dict[str, Any]:
        """Get usage summary."""
        return {
            "gemini_tokens": self.usage["gemini"],
            "gemini_pct_of_daily": (self.usage["gemini"] / self.GEMINI_DAILY_LIMIT) * 100,
            "groq_tokens": self.usage["groq"],
            "claude_tokens": self.usage["claude"],
            "total_tokens": sum(self.usage.values()),
        }

    def print_summary(self):
        """Print usage summary."""
        summary = self.get_summary()

        console.print("\n[bold cyan]Token Usage Summary[/bold cyan]")
        console.print(f"  Gemini: {summary['gemini_tokens']:,} tokens ({summary['gemini_pct_of_daily']:.1f}% of daily limit)")
        console.print(f"  Groq: {summary['groq_tokens']:,} tokens (free tier)")
        console.print(f"  Claude: {summary['claude_tokens']:,} tokens")
        console.print(f"  [bold]Total: {summary['total_tokens']:,} tokens[/bold]")


if __name__ == "__main__":
    # Test token tracking
    tracker = TokenTracker()

    # Simulate Stage 1
    tracker.log_stage(
        "Stage 1: Video Extraction",
        "gemini",
        "video file + prompt" * 1000,
        "json output" * 500,
    )

    # Simulate Stage 2
    tracker.log_stage(
        "Stage 2: Research (Gemini)",
        "gemini",
        "extraction data" * 300,
        "claims json" * 200,
    )

    tracker.log_stage(
        "Stage 2: Research (Groq)",
        "groq",
        "extraction data" * 300,
        "gaps json" * 200,
    )

    tracker.print_summary()
