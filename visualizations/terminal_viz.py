"""Terminal visualizations for pipeline outputs."""

import json
from pathlib import Path
from typing import Dict, Any
from rich.console import Console
from rich.tree import Tree
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

console = Console()


class TerminalVisualizer:
    """Display pipeline outputs in terminal."""

    def show_pipeline_progress(self, stage: str, status: str, details: str = "") -> None:
        """Show pipeline stage progress."""
        status_styles = {
            "running": "cyan",
            "complete": "green",
            "error": "red",
            "warning": "yellow",
        }
        style = status_styles.get(status, "white")

        if details:
            console.print(f"[{style}]● {stage}[/{style}] - {details}")
        else:
            console.print(f"[{style}]● {stage}[/{style}]")

    def show_consensus_summary(self, consensus_path: Path) -> None:
        """Display consensus summary as table."""
        if not consensus_path.exists():
            console.print("[yellow]Consensus data not found[/yellow]")
            return

        with open(consensus_path) as f:
            consensus = json.load(f)

        summary = consensus.get("summary", {})

        table = Table(title="Consensus Summary", show_header=True, header_style="bold cyan")
        table.add_column("Category", style="cyan")
        table.add_column("Count", justify="right", style="green")
        table.add_column("Percentage", justify="right", style="yellow")

        total = summary.get("total_claims", 0)

        categories = [
            ("High Confidence", summary.get("high_confidence_count", 0)),
            ("Single Source", summary.get("single_source_count", 0)),
            ("Disputed", summary.get("disputed_count", 0)),
        ]

        for category, count in categories:
            pct = (count / total * 100) if total > 0 else 0
            table.add_row(category, str(count), f"{pct:.1f}%")

        table.add_row("Total Claims", str(total), "100.0%", style="bold")

        console.print("\n")
        console.print(table)
        console.print("\n")

    def show_knowledge_tree(self, tree_path: Path) -> None:
        """Display tree structure."""
        if not tree_path.exists():
            console.print("[yellow]Tree data not found[/yellow]")
            return

        with open(tree_path) as f:
            tree_data = json.load(f)

        tree_root = tree_data.get("tree", {})
        metadata = tree_data.get("metadata", {})

        # Create Rich tree
        tree = Tree(f"[bold cyan]{tree_root.get('name', 'Tutorial')}[/bold cyan]")

        # Add children recursively
        self._add_tree_children(tree, tree_root.get("children", []), max_depth=2)

        console.print("\n")
        console.print(Panel(tree, title="Tutorial Structure", border_style="cyan"))
        console.print(f"\n[dim]Sections: {metadata.get('total_sections', 0)} | "
                     f"Depth: {metadata.get('depth', 0)} | "
                     f"Concepts: {metadata.get('total_concepts', 0)}[/dim]\n")

    def _add_tree_children(self, parent_node, children: list, current_depth: int = 0, max_depth: int = 2) -> None:
        """Recursively add children to tree (limit depth for readability)."""
        if current_depth >= max_depth:
            return

        for child in children[:10]:  # Limit to 10 children per level
            node_type = child.get("type", "")
            name = child.get("name", "Unknown")

            # Style by type
            if node_type == "section":
                label = f"[bold yellow]📄 {name}[/bold yellow]"
            elif node_type == "concept":
                label = f"[cyan]💡 {name}[/cyan]"
            elif node_type == "tool":
                label = f"[green]🔧 {name}[/green]"
            elif node_type == "code":
                label = f"[magenta]💻 {name}[/magenta]"
            elif node_type == "verified_claim":
                label = f"[green]✓ {name[:60]}...[/green]"
            else:
                label = f"[dim]{name}[/dim]"

            branch = parent_node.add(label)

            # Recursively add children
            if child.get("children"):
                self._add_tree_children(branch, child["children"], current_depth + 1, max_depth)

    def show_debate_summary(self, debate_path: Path) -> None:
        """Display debate summary."""
        if not debate_path.exists():
            console.print("[yellow]Debate transcript not found[/yellow]")
            return

        with open(debate_path) as f:
            debate = json.load(f)

        rounds = debate.get("rounds_completed", 0)
        transcript = debate.get("transcript", [])

        console.print("\n")
        console.print(Panel(
            f"[bold cyan]Multi-Round Debate[/bold cyan]\n\n"
            f"Rounds completed: [green]{rounds}[/green]\n"
            f"Participants: Skeptic vs Advocate\n"
            f"Moderation: Gap identification",
            title="Debate Summary",
            border_style="cyan"
        ))

        # Show brief from each round
        for round_data in transcript[:3]:  # Show first 3 rounds
            round_num = round_data.get("round", "?")
            skeptic = round_data.get("skeptic", "")[:100]
            advocate = round_data.get("advocate", "")[:100]

            console.print(f"\n[bold]Round {round_num}:[/bold]")
            console.print(f"  [red]Skeptic:[/red] {skeptic}...")
            console.print(f"  [green]Advocate:[/green] {advocate}...")

        if len(transcript) > 3:
            console.print(f"\n[dim]... and {len(transcript) - 3} more rounds[/dim]")

        console.print("\n")

    def show_graph_stats(self, graph_path: Path) -> None:
        """Display knowledge graph statistics."""
        if not graph_path.exists():
            console.print("[yellow]Knowledge graph not found[/yellow]")
            return

        with open(graph_path) as f:
            graph = json.load(f)

        metadata = graph.get("metadata", {})
        node_types = metadata.get("node_types", {})

        table = Table(title="Knowledge Graph", show_header=True, header_style="bold cyan")
        table.add_column("Node Type", style="cyan")
        table.add_column("Count", justify="right", style="green")

        for node_type, count in node_types.items():
            table.add_row(node_type.capitalize(), str(count))

        table.add_row("Total Nodes", str(metadata.get("total_nodes", 0)), style="bold")
        table.add_row("Total Edges", str(metadata.get("total_edges", 0)), style="bold")

        console.print("\n")
        console.print(table)
        console.print("\n")

    def show_full_summary(self, outputs_dir: Path = Path("outputs")) -> None:
        """Show complete visualization of all outputs."""
        console.print("\n")
        console.print(Panel.fit(
            "[bold cyan]Agentic Newsroom - Pipeline Results[/bold cyan]",
            border_style="cyan"
        ))

        # Consensus
        self.show_consensus_summary(outputs_dir.parent / "cache" / "stage2_consensus.json")

        # Debate
        self.show_debate_summary(outputs_dir / "debate_transcript.json")

        # Graph stats
        self.show_graph_stats(outputs_dir / "graph.json")

        # Tree structure
        self.show_knowledge_tree(outputs_dir / "tree.json")


if __name__ == "__main__":
    viz = TerminalVisualizer()
    viz.show_full_summary()
