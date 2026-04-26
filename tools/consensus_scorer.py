"""Consensus scoring for multi-agent research outputs."""

import json
from pathlib import Path
from typing import Dict, Any, List, Set
from collections import defaultdict
from rich.console import Console

console = Console()


class ConsensusScorer:
    """Score consensus across multiple agent outputs."""

    def __init__(self):
        self.confidence_threshold = 2  # Default: 2/3 agents must agree
        self.active_agents = 3  # Will be adjusted if agents fail

    def score(
        self,
        gemini_output: Dict[str, Any],
        groq_output: Dict[str, Any],
        claude_output: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Score consensus across agent outputs.

        Args:
            gemini_output: Agent A output
            groq_output: Agent B output (may be error dict)
            claude_output: Agent C output

        Returns:
            Consensus report with tagged claims
        """
        console.print("\n[bold cyan]Scoring consensus...[/bold cyan]")

        # Check if Groq failed
        if groq_output.get("error") == "quota_exceeded":
            console.print("  [yellow]Using 2-agent consensus (Groq unavailable)[/yellow]")
            self.active_agents = 2
            self.confidence_threshold = 1  # 1/2 agents for high confidence

        # Extract claims from each agent
        gemini_claims = self._extract_claims(gemini_output, "gemini")
        groq_claims = self._extract_claims(groq_output, "groq")
        claude_claims = self._extract_claims(claude_output, "claude")

        all_claims = gemini_claims + groq_claims + claude_claims

        # Compare claims using keyword overlap
        consensus = self._compare_claims(all_claims)

        # Tag claims by confidence
        tagged_claims = self._tag_claims(consensus)

        result = {
            "high_confidence": tagged_claims["high_confidence"],
            "single_source": tagged_claims["single_source"],
            "disputed": tagged_claims["disputed"],
            "summary": {
                "total_claims": len(all_claims),
                "high_confidence_count": len(tagged_claims["high_confidence"]),
                "single_source_count": len(tagged_claims["single_source"]),
                "disputed_count": len(tagged_claims["disputed"]),
            },
        }

        # Save to cache
        output_path = Path("cache/stage2_consensus.json")
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)

        console.print(f"\n✓ Consensus scored: {output_path}", style="green")
        console.print(f"  High confidence: {result['summary']['high_confidence_count']}")
        console.print(f"  Single source: {result['summary']['single_source_count']}")
        console.print(f"  Disputed: {result['summary']['disputed_count']}")

        return result

    def _extract_claims(self, output: Dict[str, Any], source: str) -> List[Dict[str, Any]]:
        """Extract atomic claims from agent output."""
        claims = []

        # Handle different output structures
        if "claims" in output:
            for claim in output["claims"]:
                claims.append({
                    "text": claim.get("claim", ""),
                    "source": source,
                    "evidence": claim.get("evidence", ""),
                    "confidence": claim.get("confidence", "medium"),
                })

        if "gaps" in output:
            for gap in output["gaps"]:
                claims.append({
                    "text": f"Gap: {gap}",
                    "source": source,
                    "type": "gap",
                })

        if "concerns" in output:
            for concern in output["concerns"]:
                claims.append({
                    "text": f"Concern: {concern}",
                    "source": source,
                    "type": "concern",
                })

        if "confusing_concepts" in output:
            for concept in output["confusing_concepts"]:
                claims.append({
                    "text": f"Confusing: {concept}",
                    "source": source,
                    "type": "confusion",
                })

        return claims

    def _compare_claims(self, claims: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compare claims using keyword overlap."""
        # Group similar claims
        claim_groups = defaultdict(list)

        for claim in claims:
            # Extract keywords (simple tokenization)
            keywords = self._extract_keywords(claim["text"])
            key = frozenset(keywords)
            claim_groups[key].append(claim)

        # Build consensus map
        consensus = {
            "groups": [],
        }

        for keywords, group_claims in claim_groups.items():
            sources = set(c["source"] for c in group_claims)
            consensus["groups"].append({
                "keywords": list(keywords),
                "claims": group_claims,
                "source_count": len(sources),
                "sources": list(sources),
            })

        return consensus

    def _extract_keywords(self, text: str) -> Set[str]:
        """Extract keywords from claim text (simple approach)."""
        # Remove common words and extract meaningful terms
        stopwords = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "have", "has", "had", "do", "does", "did", "will", "would",
            "should", "could", "may", "might", "must", "can", "this",
            "that", "these", "those", "to", "of", "in", "on", "at", "for",
        }

        words = text.lower().split()
        keywords = {w.strip(".,!?:;") for w in words if w not in stopwords and len(w) > 3}
        return keywords

    def _tag_claims(self, consensus: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """Tag claims by confidence level."""
        tagged = {
            "high_confidence": [],
            "single_source": [],
            "disputed": [],
        }

        for group in consensus["groups"]:
            source_count = group["source_count"]
            claims = group["claims"]

            if source_count >= self.confidence_threshold:
                # HIGH CONFIDENCE: 2+ agents agree
                tagged["high_confidence"].append({
                    "claim": claims[0]["text"],
                    "sources": group["sources"],
                    "evidence": [c.get("evidence", "") for c in claims],
                })
            elif source_count == 1:
                # SINGLE SOURCE: only 1 agent mentioned
                tagged["single_source"].append({
                    "claim": claims[0]["text"],
                    "source": claims[0]["source"],
                    "evidence": claims[0].get("evidence", ""),
                })
            else:
                # DISPUTED: contradictory information
                tagged["disputed"].append({
                    "claim": claims[0]["text"],
                    "sources": group["sources"],
                    "conflicting_views": [c["text"] for c in claims],
                })

        return tagged


if __name__ == "__main__":
    # Load agent outputs
    with open("cache/stage2_gemini.json") as f:
        gemini = json.load(f)
    with open("cache/stage2_groq.json") as f:
        groq = json.load(f)
    with open("cache/stage2_claude.json") as f:
        claude = json.load(f)

    # Score consensus
    scorer = ConsensusScorer()
    result = scorer.score(gemini, groq, claude)

    print(json.dumps(result["summary"], indent=2))
