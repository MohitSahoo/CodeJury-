"""Tree builder for hierarchical tutorial structure."""

import json
from pathlib import Path
from typing import Dict, Any, List
from rich.console import Console

console = Console()


class TreeBuilder:
    """Build hierarchical tree from tutorial structure."""

    def build(self, extraction: Dict[str, Any], consensus: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build hierarchical tree from tutorial structure.

        Args:
            extraction: Stage 1 extraction output
            consensus: Stage 2 consensus output

        Returns:
            Tree structure with nested children
        """
        console.print("\n[bold cyan]Building tree structure...[/bold cyan]")

        root = {
            "name": extraction.get("title", "Tutorial"),
            "type": "root",
            "children": []
        }

        # Level 1: Main sections from steps
        for idx, step in enumerate(extraction.get("steps", [])):
            section = {
                "name": step.get("description", f"Step {idx + 1}"),
                "type": "section",
                "timestamp": step.get("timestamp", ""),
                "children": []
            }

            # Level 2: Key points in this section
            for point in step.get("key_points", []):
                point_node = {
                    "name": point,
                    "type": "key_point",
                    "children": []
                }

                # Level 3: Related concepts
                related_concepts = self._find_related_concepts(
                    point,
                    extraction.get("key_concepts", [])
                )
                for concept in related_concepts:
                    point_node["children"].append({
                        "name": concept,
                        "type": "concept",
                    })

                section["children"].append(point_node)

            # Add code snippets as children if they exist
            code_in_section = self._find_code_for_section(
                step,
                extraction.get("code_shown", [])
            )
            for code in code_in_section:
                section["children"].append({
                    "name": f"Code: {code.get('language', 'unknown')}",
                    "type": "code",
                    "explanation": code.get("explanation", ""),
                })

            root["children"].append(section)

        # Add tools as separate branch
        if extraction.get("tools_used"):
            tools_branch = {
                "name": "Tools & Technologies",
                "type": "tools_section",
                "children": [
                    {"name": tool, "type": "tool"}
                    for tool in extraction.get("tools_used", [])
                ]
            }
            root["children"].append(tools_branch)

        # Add high confidence claims as separate branch
        if consensus.get("high_confidence"):
            claims_branch = {
                "name": "Verified Claims",
                "type": "claims_section",
                "children": [
                    {
                        "name": claim.get("claim", "")[:80],
                        "type": "verified_claim",
                        "sources": claim.get("sources", [])
                    }
                    for claim in consensus.get("high_confidence", [])[:5]  # Top 5
                ]
            }
            root["children"].append(claims_branch)

        tree = {
            "tree": root,
            "metadata": {
                "total_sections": len(extraction.get("steps", [])),
                "total_concepts": len(extraction.get("key_concepts", [])),
                "total_tools": len(extraction.get("tools_used", [])),
                "depth": self._calculate_depth(root),
            }
        }

        # Save to outputs
        output_path = Path("outputs/tree.json")
        output_path.parent.mkdir(exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(tree, f, indent=2)

        console.print(f"✓ Tree structure: {output_path}", style="green")
        console.print(f"  Sections: {tree['metadata']['total_sections']}, Depth: {tree['metadata']['depth']}")

        return tree

    def _find_related_concepts(self, text: str, concepts: List[str]) -> List[str]:
        """Find concepts related to text."""
        text_lower = text.lower()
        related = []

        for concept in concepts:
            if concept.lower() in text_lower:
                related.append(concept)

        return related[:3]  # Max 3 concepts per point

    def _find_code_for_section(self, step: Dict[str, Any], all_code: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find code snippets related to this section."""
        # Simple heuristic: match by timestamp or description keywords
        step_desc = step.get("description", "").lower()
        related_code = []

        for code in all_code:
            code_explanation = code.get("explanation", "").lower()
            if any(word in code_explanation for word in step_desc.split()[:5]):
                related_code.append(code)

        return related_code[:2]  # Max 2 code snippets per section

    def _calculate_depth(self, node: Dict[str, Any], current_depth: int = 0) -> int:
        """Calculate maximum depth of tree."""
        if not node.get("children"):
            return current_depth

        max_child_depth = current_depth
        for child in node.get("children", []):
            child_depth = self._calculate_depth(child, current_depth + 1)
            max_child_depth = max(max_child_depth, child_depth)

        return max_child_depth


if __name__ == "__main__":
    # Load extraction and consensus
    with open("cache/stage1_extraction.json") as f:
        extraction = json.load(f)
    with open("cache/stage2_consensus.json") as f:
        consensus = json.load(f)

    # Build tree
    builder = TreeBuilder()
    tree = builder.build(extraction, consensus)

    print(json.dumps(tree["metadata"], indent=2))
