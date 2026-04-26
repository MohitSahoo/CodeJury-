"""Stage 4: Editor agent with verification loop."""

import json
from pathlib import Path
from typing import Dict, Any, List
from rich.console import Console

console = Console()


class EditorAgent:
    """Write and verify technical blog post draft."""

    MAX_PASSES = 3

    def __init__(self):
        self.verification_tags = {
            "verified": "[✅ VERIFIED]",
            "unverified": "[⚠️ UNVERIFIED]",
            "disputed": "[❌ DISPUTED]",
        }

    def edit(
        self,
        editorial_brief: str,
        consensus: Dict[str, Any],
        extraction: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Write verified draft with iterative verification.

        Args:
            editorial_brief: Stage 3 editorial guidance
            consensus: Stage 2 consensus claims
            extraction: Stage 1 video extraction

        Returns:
            Verified draft with metadata
        """
        console.print("\n[bold cyan]Stage 4: Editor Agent[/bold cyan]\n")

        # Pass 1: Write first draft with verification tags
        console.print("[bold]Pass 1: Writing first draft[/bold]")
        draft = self._write_first_draft(editorial_brief, consensus, extraction)

        # Passes 2-3: Resolve verification flags
        for pass_num in range(2, self.MAX_PASSES + 1):
            console.print(f"\n[bold]Pass {pass_num}: Resolving verification flags[/bold]")

            unresolved = self._count_flags(draft)
            if unresolved["unverified"] == 0 and unresolved["disputed"] == 0:
                console.print("  ✓ All flags resolved!", style="green")
                break

            console.print(f"  Unverified: {unresolved['unverified']}, Disputed: {unresolved['disputed']}")
            draft = self._resolve_flags(draft, consensus, extraction, pass_num)

        # Move remaining unresolved to appendix
        final_draft, reviewer_notes = self._finalize_draft(draft)

        result = {
            "draft": final_draft,
            "reviewer_notes": reviewer_notes,
            "stats": {
                "word_count": len(final_draft.split()),
                "verified_claims": draft.count(self.verification_tags["verified"]),
                "unresolved_flags": len(reviewer_notes),
            },
        }

        # Save to cache
        output_path = Path("cache/stage4_verified.md")
        with open(output_path, "w") as f:
            f.write(final_draft)
            if reviewer_notes:
                f.write("\n\n---\n\n## Reviewer Notes\n\n")
                for note in reviewer_notes:
                    f.write(f"- {note}\n")

        console.print(f"\n✓ Draft complete: {output_path}", style="green")
        console.print(f"  Word count: {result['stats']['word_count']}")
        console.print(f"  Verified claims: {result['stats']['verified_claims']}")
        console.print(f"  Unresolved flags: {result['stats']['unresolved_flags']}")

        return result

    def _write_first_draft(
        self,
        editorial_brief: str,
        consensus: Dict[str, Any],
        extraction: Dict[str, Any],
    ) -> str:
        """
        Write first draft with verification tags.

        This is a prompt template. In production, call Claude API.
        """
        high_confidence = consensus["high_confidence"]
        single_source = consensus["single_source"]
        disputed = consensus["disputed"]

        draft_prompt = f"""PROMPT FOR CLAUDE:
Write a technical blog post based on this tutorial analysis.

Tutorial: {extraction['title']}
Summary: {extraction['summary']}

Editorial Brief:
{editorial_brief}

Consensus Claims:
- HIGH CONFIDENCE ({len(high_confidence)} claims): {json.dumps(high_confidence[:3], indent=2)}
- SINGLE SOURCE ({len(single_source)} claims): {json.dumps(single_source[:3], indent=2)}
- DISPUTED ({len(disputed)} claims): {json.dumps(disputed[:3], indent=2)}

Instructions:
1. Write a clear, structured blog post following the editorial brief
2. Tag all claims with verification status:
   - {self.verification_tags['verified']} for HIGH CONFIDENCE claims
   - {self.verification_tags['unverified']} for SINGLE SOURCE claims
   - {self.verification_tags['disputed']} for DISPUTED claims
3. Include code examples from: {json.dumps(extraction['code_shown'][:2], indent=2)}
4. Structure with H2 sections, no H3 unless necessary
5. Add "Prerequisites" section if needed
6. Keep under 1500 words

Return the draft in markdown format with inline verification tags."""

        # For now, return a template draft
        return f"""# {extraction['title']}

{extraction['summary']} {self.verification_tags['verified']}

## Prerequisites

{', '.join(extraction['prerequisites'])} {self.verification_tags['verified']}

## Overview

This tutorial covers {', '.join(extraction['key_concepts'][:3])}. {self.verification_tags['unverified']}

## Step-by-Step Guide

### Step 1: Setup

First, install the required tools: {', '.join(extraction['tools_used'])}. {self.verification_tags['verified']}

[Additional steps would be generated here based on extraction['steps']]

### Step 2: Implementation

{self.verification_tags['unverified']} The implementation follows best practices for production use.

## Common Pitfalls

{self.verification_tags['disputed']} Some developers report issues with configuration.

## Key Takeaways

- {extraction['key_concepts'][0]} {self.verification_tags['verified']}
- Advanced usage requires additional setup {self.verification_tags['unverified']}
"""

    def _count_flags(self, draft: str) -> Dict[str, int]:
        """Count verification flags in draft."""
        return {
            "verified": draft.count(self.verification_tags["verified"]),
            "unverified": draft.count(self.verification_tags["unverified"]),
            "disputed": draft.count(self.verification_tags["disputed"]),
        }

    def _resolve_flags(
        self,
        draft: str,
        consensus: Dict[str, Any],
        extraction: Dict[str, Any],
        pass_num: int,
    ) -> str:
        """
        Attempt to resolve verification flags.

        This is a prompt template. In production, call Claude API.
        """
        # For now, simulate resolution by converting some flags
        # In production, this would re-analyze claims and update tags

        if pass_num == 2:
            # Resolve some UNVERIFIED by finding supporting evidence
            draft = draft.replace(
                f"This tutorial covers {', '.join(extraction['key_concepts'][:3])}. {self.verification_tags['unverified']}",
                f"This tutorial covers {', '.join(extraction['key_concepts'][:3])}. {self.verification_tags['verified']}",
                1,
            )

        return draft

    def _finalize_draft(self, draft: str) -> tuple[str, List[str]]:
        """
        Finalize draft by moving unresolved flags to appendix.

        Returns:
            Tuple of (clean_draft, reviewer_notes)
        """
        reviewer_notes = []

        # Extract lines with unresolved flags
        lines = draft.split("\n")
        clean_lines = []

        for line in lines:
            if self.verification_tags["unverified"] in line:
                # Move to reviewer notes
                clean_text = line.replace(self.verification_tags["unverified"], "").strip()
                reviewer_notes.append(f"UNVERIFIED: {clean_text}")
                # Keep line but remove tag
                clean_lines.append(line.replace(self.verification_tags["unverified"], ""))

            elif self.verification_tags["disputed"] in line:
                # Move to reviewer notes
                clean_text = line.replace(self.verification_tags["disputed"], "").strip()
                reviewer_notes.append(f"DISPUTED: {clean_text}")
                # Keep line but remove tag
                clean_lines.append(line.replace(self.verification_tags["disputed"], ""))

            else:
                # Keep verified claims and remove tags
                clean_lines.append(line.replace(self.verification_tags["verified"], ""))

        return "\n".join(clean_lines), reviewer_notes


if __name__ == "__main__":
    # Load Stage 3 debate
    with open("cache/stage3_debate.json") as f:
        debate = json.load(f)

    # Load Stage 2 consensus
    with open("cache/stage2_consensus.json") as f:
        consensus = json.load(f)

    # Load Stage 1 extraction
    with open("cache/stage1_extraction.json") as f:
        extraction = json.load(f)

    # Run editor
    editor = EditorAgent()
    result = editor.edit(
        debate["editorial_brief"],
        consensus,
        extraction,
    )

    print("\n" + "=" * 60)
    print("EDITOR COMPLETE")
    print("=" * 60)
    print(f"\nStats: {json.dumps(result['stats'], indent=2)}")
