#!/usr/bin/env python3
"""Quick test script for Phase 1-2 implementation."""

import sys
from pathlib import Path

def check_files():
    """Check all new files exist."""
    print("Checking implementation files...")

    files = [
        "agents/debate_room.py",
        "agents/video_extractor.py",
        "orchestrator.py",
        "tools/knowledge_graph_builder.py",
        "tools/tree_builder.py",
        "visualizations/terminal_viz.py",
        "verify_implementation.py",
        "USAGE_GUIDE.md",
        "IMPLEMENTATION.md",
    ]

    all_exist = True
    for file in files:
        path = Path(file)
        if path.exists():
            print(f"✓ {file}")
        else:
            print(f"✗ {file} - MISSING")
            all_exist = False

    return all_exist

def check_imports():
    """Check key imports work."""
    print("\nChecking imports...")

    try:
        from tools.knowledge_graph_builder import KnowledgeGraphBuilder
        print("✓ KnowledgeGraphBuilder")
    except ImportError as e:
        print(f"✗ KnowledgeGraphBuilder: {e}")
        return False

    try:
        from tools.tree_builder import TreeBuilder
        print("✓ TreeBuilder")
    except ImportError as e:
        print(f"✗ TreeBuilder: {e}")
        return False

    try:
        from visualizations.terminal_viz import TerminalVisualizer
        print("✓ TerminalVisualizer")
    except ImportError as e:
        print(f"✗ TerminalVisualizer: {e}")
        return False

    try:
        from agents.debate_room import DebateRoom
        print("✓ DebateRoom (refactored)")
    except ImportError as e:
        print(f"✗ DebateRoom: {e}")
        return False

    return True

def main():
    print("=" * 60)
    print("Phase 1-2 Implementation Test")
    print("=" * 60)
    print()

    files_ok = check_files()
    imports_ok = check_imports()

    print("\n" + "=" * 60)
    if files_ok and imports_ok:
        print("✓ Implementation verified!")
        print("\nNext steps:")
        print("1. Run pipeline: python orchestrator.py --url <youtube_url>")
        print("2. Check outputs: python verify_implementation.py")
        print("3. View guide: cat USAGE_GUIDE.md")
        return 0
    else:
        print("✗ Implementation has issues")
        return 1

if __name__ == "__main__":
    sys.exit(main())
