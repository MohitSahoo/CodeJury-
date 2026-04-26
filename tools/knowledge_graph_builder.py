"""Knowledge graph builder for tutorial content."""

import json
from pathlib import Path
from typing import Dict, Any, List, Set
from rich.console import Console

console = Console()


class KnowledgeGraphBuilder:
    """Build knowledge graph from consensus and extraction."""

    def build(self, consensus: Dict[str, Any], extraction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build knowledge graph from consensus and extraction.

        Args:
            consensus: Stage 2 consensus output
            extraction: Stage 1 extraction output

        Returns:
            Knowledge graph with nodes and edges
        """
        console.print("\n[bold cyan]Building knowledge graph...[/bold cyan]")

        nodes = []
        edges = []
        node_ids = set()

        # Add concept nodes
        for concept in extraction.get("key_concepts", []):
            node_id = self._make_id("concept", concept)
            if node_id not in node_ids:
                nodes.append({
                    "id": node_id,
                    "type": "concept",
                    "label": concept,
                })
                node_ids.add(node_id)

        # Add tool nodes
        for tool in extraction.get("tools_used", []):
            node_id = self._make_id("tool", tool)
            if node_id not in node_ids:
                nodes.append({
                    "id": node_id,
                    "type": "tool",
                    "label": tool,
                })
                node_ids.add(node_id)

        # Add high confidence claim nodes
        for claim_obj in consensus.get("high_confidence", []):
            claim = claim_obj.get("claim", "")
            node_id = self._make_id("claim", claim)
            if node_id not in node_ids:
                nodes.append({
                    "id": node_id,
                    "type": "claim",
                    "label": claim[:100],  # Truncate long claims
                    "confidence": "high",
                    "sources": claim_obj.get("sources", []),
                })
                node_ids.add(node_id)

                # Connect claims to related concepts
                edges.extend(self._find_concept_edges(node_id, claim, extraction.get("key_concepts", [])))

        # Add single source claim nodes
        for claim_obj in consensus.get("single_source", []):
            claim = claim_obj.get("claim", "")
            node_id = self._make_id("claim", claim)
            if node_id not in node_ids:
                nodes.append({
                    "id": node_id,
                    "type": "claim",
                    "label": claim[:100],
                    "confidence": "single_source",
                    "source": claim_obj.get("source", ""),
                })
                node_ids.add(node_id)

                edges.extend(self._find_concept_edges(node_id, claim, extraction.get("key_concepts", [])))

        # Connect tools to concepts they implement
        for tool in extraction.get("tools_used", []):
            tool_id = self._make_id("tool", tool)
            for concept in extraction.get("key_concepts", []):
                if self._tools_relate_to_concept(tool, concept):
                    concept_id = self._make_id("concept", concept)
                    edges.append({
                        "source": tool_id,
                        "target": concept_id,
                        "type": "implements",
                    })

        graph = {
            "nodes": nodes,
            "edges": edges,
            "metadata": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "node_types": self._count_node_types(nodes),
            }
        }

        # Save to outputs
        output_path = Path("outputs/graph.json")
        output_path.parent.mkdir(exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(graph, f, indent=2)

        console.print(f"✓ Knowledge graph: {output_path}", style="green")
        console.print(f"  Nodes: {len(nodes)}, Edges: {len(edges)}")

        return graph

    def _make_id(self, node_type: str, label: str) -> str:
        """Create unique node ID."""
        return f"{node_type}_{hash(label) % 100000}"

    def _find_concept_edges(self, claim_id: str, claim_text: str, concepts: List[str]) -> List[Dict[str, Any]]:
        """Find edges between claim and related concepts."""
        edges = []
        claim_lower = claim_text.lower()

        for concept in concepts:
            # Simple keyword matching
            if concept.lower() in claim_lower:
                concept_id = self._make_id("concept", concept)
                edges.append({
                    "source": claim_id,
                    "target": concept_id,
                    "type": "references",
                })

        return edges

    def _tools_relate_to_concept(self, tool: str, concept: str) -> bool:
        """Check if tool relates to concept (simple heuristic)."""
        tool_lower = tool.lower()
        concept_lower = concept.lower()

        # Check if tool name appears in concept or vice versa
        return tool_lower in concept_lower or concept_lower in tool_lower

    def _count_node_types(self, nodes: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count nodes by type."""
        counts = {}
        for node in nodes:
            node_type = node.get("type", "unknown")
            counts[node_type] = counts.get(node_type, 0) + 1
        return counts


if __name__ == "__main__":
    # Load consensus and extraction
    with open("cache/stage2_consensus.json") as f:
        consensus = json.load(f)
    with open("cache/stage1_extraction.json") as f:
        extraction = json.load(f)

    # Build graph
    builder = KnowledgeGraphBuilder()
    graph = builder.build(consensus, extraction)

    print(json.dumps(graph["metadata"], indent=2))
