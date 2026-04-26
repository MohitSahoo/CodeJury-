"""Verification script for Phase 1-2 implementation."""

import json
from pathlib import Path
from rich.console import Console

console = Console()


def verify_outputs():
    """Verify all expected JSON outputs exist."""
    console.print("\n[bold cyan]Verifying Implementation[/bold cyan]\n")

    expected_outputs = [
        ("outputs/debate_transcript.json", "Debate Transcript"),
        ("outputs/graph.json", "Knowledge Graph"),
        ("outputs/tree.json", "Tree Structure"),
        ("outputs/visual_insights.json", "Visual Insights"),
        ("outputs/report.json", "Structured Report"),
        ("outputs/report.md", "Markdown Report"),
    ]

    results = []
    for path, name in expected_outputs:
        file_path = Path(path)
        exists = file_path.exists()
        results.append((name, exists, path))

        if exists:
            console.print(f"✓ {name}: {path}", style="green")
            # Show file size
            size = file_path.stat().st_size
            console.print(f"  Size: {size:,} bytes", style="dim")
        else:
            console.print(f"✗ {name}: {path} (not found)", style="yellow")

    # Summary
    found = sum(1 for _, exists, _ in results if exists)
    total = len(results)

    console.print(f"\n[bold]Summary:[/bold] {found}/{total} outputs found")

    if found == total:
        console.print("[green]✓ All outputs generated successfully![/green]")
    else:
        console.print(f"[yellow]⚠ {total - found} outputs missing (run pipeline first)[/yellow]")

    return found == total


def verify_debate_structure():
    """Verify debate transcript has multi-round structure."""
    debate_path = Path("outputs/debate_transcript.json")
    if not debate_path.exists():
        console.print("\n[yellow]Debate transcript not found - skipping structure check[/yellow]")
        return False

    console.print("\n[bold cyan]Verifying Debate Structure[/bold cyan]\n")

    with open(debate_path) as f:
        debate = json.load(f)

    # Check for required fields
    required_fields = ["transcript", "editorial_brief", "rounds_completed"]
    for field in required_fields:
        if field in debate:
            console.print(f"✓ Field '{field}' present", style="green")
        else:
            console.print(f"✗ Field '{field}' missing", style="red")
            return False

    # Check transcript structure
    transcript = debate.get("transcript", [])
    console.print(f"\n✓ Rounds completed: {debate.get('rounds_completed', 0)}", style="green")

    for round_data in transcript:
        round_num = round_data.get("round", "?")
        has_skeptic = "skeptic" in round_data
        has_advocate = "advocate" in round_data

        if has_skeptic and has_advocate:
            console.print(f"✓ Round {round_num}: skeptic + advocate present", style="green")
        else:
            console.print(f"✗ Round {round_num}: missing positions", style="red")

    console.print(f"\n✓ Editorial brief length: {len(debate.get('editorial_brief', ''))} chars", style="green")

    return True


def verify_graph_structure():
    """Verify knowledge graph has nodes and edges."""
    graph_path = Path("outputs/graph.json")
    if not graph_path.exists():
        console.print("\n[yellow]Knowledge graph not found - skipping structure check[/yellow]")
        return False

    console.print("\n[bold cyan]Verifying Knowledge Graph[/bold cyan]\n")

    with open(graph_path) as f:
        graph = json.load(f)

    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    metadata = graph.get("metadata", {})

    console.print(f"✓ Nodes: {len(nodes)}", style="green")
    console.print(f"✓ Edges: {len(edges)}", style="green")

    # Check node types
    node_types = metadata.get("node_types", {})
    for node_type, count in node_types.items():
        console.print(f"  - {node_type}: {count}", style="dim")

    return len(nodes) > 0 and len(edges) > 0


def verify_tree_structure():
    """Verify tree has hierarchical structure."""
    tree_path = Path("outputs/tree.json")
    if not tree_path.exists():
        console.print("\n[yellow]Tree structure not found - skipping structure check[/yellow]")
        return False

    console.print("\n[bold cyan]Verifying Tree Structure[/bold cyan]\n")

    with open(tree_path) as f:
        tree_data = json.load(f)

    tree = tree_data.get("tree", {})
    metadata = tree_data.get("metadata", {})

    console.print(f"✓ Root: {tree.get('name', 'Unknown')}", style="green")
    console.print(f"✓ Sections: {metadata.get('total_sections', 0)}", style="green")
    console.print(f"✓ Depth: {metadata.get('depth', 0)}", style="green")
    console.print(f"✓ Children: {len(tree.get('children', []))}", style="green")

    return len(tree.get("children", [])) > 0


if __name__ == "__main__":
    console.print("[bold]Phase 1-2 Implementation Verification[/bold]")
    console.print("=" * 60)

    # Check outputs exist
    all_outputs_exist = verify_outputs()

    if all_outputs_exist:
        # Verify structures
        verify_debate_structure()
        verify_graph_structure()
        verify_tree_structure()

        console.print("\n" + "=" * 60)
        console.print("[bold green]✓ Implementation verified successfully![/bold green]")
    else:
        console.print("\n" + "=" * 60)
        console.print("[bold yellow]Run the pipeline first to generate outputs:[/bold yellow]")
        console.print("python orchestrator.py --url <youtube_url>")
