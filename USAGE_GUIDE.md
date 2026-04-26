# Phase 1-2 Usage Guide

## Quick Start

### Run Pipeline with Visualizations

```bash
cd /Users/mohitsahoo/Desktop/Aiagents/agentic-newsroom

# Run with terminal visualizations (default)
python orchestrator.py --url "https://www.youtube.com/watch?v=VIDEO_ID"

# Run without visualizations
python orchestrator.py --url "https://www.youtube.com/watch?v=VIDEO_ID" --viz none

# Force re-run (ignore cache)
python orchestrator.py --url "https://www.youtube.com/watch?v=VIDEO_ID" --force
```

## New Outputs

After running the pipeline, check `outputs/` directory:

### 1. Debate Transcript (`debate_transcript.json`)

Multi-round debate between Skeptic and Advocate:

```bash
# View rounds completed
cat outputs/debate_transcript.json | jq '.rounds_completed'

# View first round
cat outputs/debate_transcript.json | jq '.transcript[0]'

# View editorial brief
cat outputs/debate_transcript.json | jq -r '.editorial_brief'
```

**Structure:**
- `transcript[]`: Array of debate rounds
  - `round`: Round number
  - `skeptic`: Skeptic's position
  - `advocate`: Advocate's position
  - `gaps_addressed`: Gaps being addressed (rounds 2+)
- `editorial_brief`: Final synthesis
- `rounds_completed`: Total rounds

### 2. Knowledge Graph (`graph.json`)

Nodes and edges representing tutorial concepts:

```bash
# View graph stats
cat outputs/graph.json | jq '.metadata'

# View all nodes
cat outputs/graph.json | jq '.nodes[]'

# View all edges
cat outputs/graph.json | jq '.edges[]'

# Count node types
cat outputs/graph.json | jq '.metadata.node_types'
```

**Structure:**
- `nodes[]`: Concepts, tools, claims
  - `id`: Unique identifier
  - `type`: concept/tool/claim
  - `label`: Display name
  - `confidence`: high/single_source (for claims)
- `edges[]`: Relationships
  - `source`: Source node ID
  - `target`: Target node ID
  - `type`: references/implements

### 3. Tree Structure (`tree.json`)

Hierarchical tutorial structure:

```bash
# View tree metadata
cat outputs/tree.json | jq '.metadata'

# View root and first level
cat outputs/tree.json | jq '.tree | {name, children: .children[].name}'

# View full tree (pretty print)
cat outputs/tree.json | jq '.tree'
```

**Structure:**
- `tree`: Root node
  - `name`: Tutorial title
  - `type`: root
  - `children[]`: Sections
    - `name`: Section description
    - `timestamp`: Video timestamp
    - `children[]`: Key points and concepts

### 4. Visual Insights (`visual_insights.json`)

Visual-specific findings from video:

```bash
# View frame analysis
cat outputs/visual_insights.json | jq '.frame_analysis'

# View visual highlights
cat outputs/visual_insights.json | jq '.visual_highlights[]'

# View detected UI elements
cat outputs/visual_insights.json | jq '.ui_elements_detected[]'
```

**Structure:**
- `on_screen_code[]`: Code snippets shown
- `visual_highlights[]`: Key visual moments with timestamps
- `ui_elements_detected[]`: UI interactions
- `diagrams_detected[]`: Diagrams/charts shown
- `frame_analysis`: Summary statistics

### 5. Structured Report (`report.json`)

Complete report metadata:

```bash
# View metadata
cat outputs/report.json | jq '.metadata'

# View verification stats
cat outputs/report.json | jq '.verification'

# View verification score
cat outputs/report.json | jq '.metadata.verification_score'
```

**Structure:**
- `metadata`: Title, source, timestamp, word count, verification score
- `content`: Summary, sections, code snippets, key takeaways
- `verification`: Verified/unverified/disputed claim counts
- `tools_and_concepts`: Complete lists

## Terminal Visualizations

When running with `--viz terminal` (default), you'll see:

1. **Consensus Summary Table**
   - High confidence claims
   - Single source claims
   - Disputed claims
   - Percentages

2. **Debate Summary**
   - Rounds completed
   - Brief from each round
   - Participants

3. **Knowledge Graph Stats**
   - Node counts by type
   - Total edges

4. **Tutorial Tree Structure**
   - Hierarchical view with icons
   - Sections, concepts, tools
   - Limited depth for readability

## Verification

Run verification script to check all outputs:

```bash
python verify_implementation.py
```

This checks:
- All 6 output files exist
- Debate has multi-round structure
- Graph has nodes and edges
- Tree has hierarchical structure

## Standalone Visualization

View visualizations without re-running pipeline:

```bash
cd visualizations
python terminal_viz.py
```

## Examples

### Example 1: View Debate Rounds

```bash
# Count rounds
jq '.rounds_completed' outputs/debate_transcript.json

# View skeptic position from round 1
jq -r '.transcript[0].skeptic' outputs/debate_transcript.json

# View advocate position from round 1
jq -r '.transcript[0].advocate' outputs/debate_transcript.json
```

### Example 2: Explore Knowledge Graph

```bash
# List all concepts
jq -r '.nodes[] | select(.type=="concept") | .label' outputs/graph.json

# List all tools
jq -r '.nodes[] | select(.type=="tool") | .label' outputs/graph.json

# Count high confidence claims
jq '[.nodes[] | select(.type=="claim" and .confidence=="high")] | length' outputs/graph.json
```

### Example 3: Navigate Tree

```bash
# List all sections
jq -r '.tree.children[] | select(.type=="section") | .name' outputs/tree.json

# View first section with timestamp
jq '.tree.children[0] | {name, timestamp}' outputs/tree.json
```

## Troubleshooting

### Missing Outputs

If some outputs are missing:

```bash
# Check which stages completed
ls -la cache/

# Re-run with force flag
python orchestrator.py --url "YOUR_URL" --force
```

### Visualization Not Showing

```bash
# Ensure visualizations directory exists
ls -la visualizations/

# Run verification
python verify_implementation.py

# Try standalone visualization
cd visualizations && python terminal_viz.py
```

### Graph/Tree Empty

If graph or tree has no data:
- Ensure Stage 2 consensus completed
- Check `cache/stage2_consensus.json` exists
- Re-run pipeline with `--force`

## Next Steps

1. **Explore outputs:** Use jq commands above to inspect JSON files
2. **Customize:** Modify builders in `tools/` to adjust graph/tree structure
3. **Visualize:** Run with `--viz terminal` to see rich terminal output
4. **Verify:** Run `verify_implementation.py` to check implementation

## Phase 3+ Features (Coming Soon)

- Web dashboard with D3.js graphs
- Multi-video comparison
- Different content sources (GitHub, blogs, podcasts)
- Output format conversion (Twitter threads, slides)
