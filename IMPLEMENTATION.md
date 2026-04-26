# Agentic Newsroom - Implementation Roadmap

## Overview
5-session build plan for multi-agent YouTube-to-blog pipeline. Each session is self-contained with verification steps.

---

## Session 1: Project Scaffold ✅ COMPLETE

### Goals
- Set up directory structure
- Configure environment and dependencies
- Initialize instruction ledger
- Test yt-dlp installation

### Steps
1. Create directory structure: `agents/`, `tools/`, `outputs/`, `cache/`
2. Create `.env.example` with API key templates
3. Create `.gitignore` (ignore `.env` and `cache/`)
4. Create `claude.md` instruction ledger with default schema
5. Create `requirements.txt` with pinned dependencies
6. Install yt-dlp and verify it works
7. Git init and first commit

### Verification
- [ ] All directories exist
- [ ] `.env.example` created, `.env` in `.gitignore`
- [ ] `yt-dlp --print title <youtube-url>` works
- [ ] Git repository initialized

### Files Created
- `claude.md` - Instruction ledger
- `.env.example` - API key template
- `.gitignore` - Ignore patterns
- `requirements.txt` - Python dependencies
- `README.md` - Project documentation

---

## Session 2: Stage 1 - Video Extraction ✅ COMPLETE

### Goals
- Download YouTube videos with yt-dlp
- Extract video content using Gemini API
- Cache results to avoid re-uploading
- Enforce 15-minute video cap

### Steps
1. Create `tools/youtube_downloader.py`:
   - Wrapper around yt-dlp
   - Download video + transcript to `cache/`
   - Progress bar with rich library
   - Return video path, transcript path, duration

2. Create `agents/video_extractor.py`:
   - Check if `cache/stage1_extraction.json` exists (skip if yes)
   - Call youtube_downloader
   - Enforce 15-min duration cap
   - Upload video to Gemini `gemini-1.5-flash`
   - Extract structured JSON:
     - title, summary
     - steps with timestamps
     - code_shown, tools_used
     - prerequisites, key_concepts
   - Save to `cache/stage1_extraction.json`
   - Add 4-second sleep after Gemini call (15 RPM limit)

3. Create standalone test script `test_stage1.py`

### Verification
- [ ] Run with real 5-10 min YouTube tutorial URL
- [ ] `cache/video.mp4` and `cache/transcript.txt` exist
- [ ] `cache/stage1_extraction.json` contains valid JSON with all fields
- [ ] Second run skips video upload (uses cached result)
- [ ] Videos >15 min rejected with clear error

### Files Created
- `tools/youtube_downloader.py`
- `agents/video_extractor.py`
- `test_stage1.py`

---

## Session 3: Stage 2 - Multi-Agent Research ✅ COMPLETE

### Goals
- Run 3 research agents with different perspectives
- Compare outputs and score consensus
- Track token usage

### Steps
1. Create `agents/research_agent.py`:
   - Agent A: Gemini flash (temp=0.3, neutral extractor)
     - Extract technical claims with timestamp evidence
     - Save to `cache/stage2_gemini.json`
   - Agent B: Groq llama-3.3-70b-versatile (temp=0.6, skeptical engineer)
     - Find gaps, assumptions, potential errors
     - Save to `cache/stage2_groq.json`
     - Minimal rate limiting (Groq is fast)
   - Agent C: Claude prompt (practical educator)
     - Identify beginner confusion points
     - Save to `cache/stage2_claude.json`
   - Run sequentially (not parallel)

2. Create `tools/consensus_scorer.py`:
   - Parse each agent output into atomic claims
   - Compare using keyword overlap (no embeddings)
   - Tag claims:
     - HIGH CONFIDENCE (2+ agents agree)
     - SINGLE SOURCE (1 agent only)
     - DISPUTED (contradictions)
   - Save to `cache/stage2_consensus.json`

3. Create `tools/token_tracker.py`:
   - Estimate tokens per API call
   - Log usage per stage
   - Warn at 80% of daily limits (800K Gemini)

4. Create test script `test_stage2.py`

### Verification
- [ ] Run Stage 2 with cached Stage 1 output
- [ ] 3 agent outputs in cache with different perspectives
- [ ] Consensus scorer produces all 3 tag types
- [ ] Token tracker logs usage and warns appropriately
- [ ] Total tokens <15K for 10-min video

### Files Created
- `agents/research_agent.py`
- `tools/consensus_scorer.py`
- `tools/token_tracker.py`
- `test_stage2.py`

---

## Session 4: Stages 3 & 4 - Debate and Verification ✅ COMPLETE

### Goals
- Run 4-persona debate to synthesize research
- Write verified draft with inline tags
- Resolve verification flags iteratively

### Steps
1. Create `agents/debate_room.py`:
   - Sequential Claude prompts with 4 personas:
     1. Skeptical Reviewer (find weak claims)
     2. Beginner Educator (simplify complex parts)
     3. SEO Strategist (structure for readers)
     4. Mediator (synthesize into editorial brief)
   - Each persona: 200-word limit per turn
   - Input: consensus brief from Stage 2
   - Save full transcript to `cache/stage3_debate.json`

2. Create `agents/editor_agent.py`:
   - Input: editorial brief + consensus claims + stage1 extraction
   - Write first draft with verification tags:
     - [✅ VERIFIED] - HIGH CONFIDENCE claims
     - [⚠️ UNVERIFIED] - SINGLE SOURCE claims
     - [❌ DISPUTED] - contradictory claims
   - Loop up to 3 passes to resolve flags:
     - Try to verify UNVERIFIED claims
     - Resolve or remove DISPUTED claims
   - After 3 passes, move unresolved to "Reviewer Notes" appendix
   - Save to `cache/stage4_verified.md`

3. Create test script `test_stage34.py`

### Verification
- [ ] Run Stages 3-4 with Stage 2 consensus output
- [ ] Debate transcript has 4 distinct persona voices
- [ ] Verified draft has inline tags
- [ ] Unresolved items in appendix (not inline)
- [ ] Draft is readable and well-structured

### Files Created
- `agents/debate_room.py`
- `agents/editor_agent.py`
- `test_stage34.py`

---

## Session 5: Stage 5 + Orchestrator + End-to-End ✅ COMPLETE

### Goals
- Create main orchestrator CLI
- Generate final clean report
- Implement feedback collection and ledger updates
- Test full pipeline end-to-end

### Steps
1. Create `orchestrator.py`:
   - CLI entry: `python orchestrator.py --url "https://youtube.com/..."`
   - Load `claude.md` at start
   - Call stages 1-5 in sequence
   - Fail fast on errors with clear messages:
     - Show which stage failed
     - Show error type (rate limit, auth, timeout)
     - Show how to resume (which cache files exist)
   - Print summary:
     - Word count
     - Verified % (HIGH CONFIDENCE / total claims)
     - Disputed items count
     - Token usage breakdown
   - Prompt for feedback
   - Pass feedback to ledger updater

2. Create `tools/ledger_updater.py`:
   - Parse `claude.md` sections
   - Append timestamped feedback to "Session Feedback Log"
   - Auto-archive entries older than 60 days

3. Generate final report:
   - Load `claude.md` style preferences
   - Remove all verification tags
   - Apply formatting rules (H2/H3, Key Takeaways box)
   - Save to `outputs/report.md`

4. Create comprehensive test script `test_full_pipeline.py`

### Verification
- [ ] Run full pipeline: `python orchestrator.py --url "<youtube-url>"`
- [ ] `outputs/report.md` is clean, well-structured, matches style
- [ ] Summary shows accurate metrics
- [ ] Feedback collection works
- [ ] Feedback appends to `claude.md`
- [ ] Second run loads `claude.md` and affects output
- [ ] Error handling: test with invalid API key, verify clear error
- [ ] Pipeline completes in <10 minutes for 5-10 min video

### Success Criteria
- Pipeline completes in under 10 minutes for 5-10 min video
- Final report requires <3 manual edits per 1000 words
- Consensus filter flags 75%+ of known hallucinations
- Second run with feedback shows measurable style changes

### Files Created
- `orchestrator.py`
- `tools/ledger_updater.py`
- `test_full_pipeline.py`

---

## Token Budget (per run)

| Stage | Gemini | Groq | Claude | Total |
|-------|--------|--------|--------|-------|
| Stage 1: Video Extraction | 6K | 0 | 0 | 6K |
| Stage 2: Research | 2K | 2K | 1K | 5K |
| Stage 3: Debate | 0 | 0 | 8K | 8K |
| Stage 4: Verification | 0 | 2K | 6K | 8K |
| Stage 5: Final Report | 0 | 0 | 5K | 5K |
| **Total** | **8K** | **4K** | **20K** | **32K** |

Free tier limits:
- Gemini: 1M tokens/day (125 runs)
- Groq: Free tier with generous limits
- Claude: No hard limit

---

## Error Handling Strategy

### Fail Fast Principles
1. Check API keys exist before starting
2. Validate yt-dlp success before proceeding
3. Stop immediately on API errors
4. Show clear error messages with:
   - Which stage failed
   - Error type
   - How to resume
5. No auto-retry, no silent failures

### Resumability
- Each stage saves to cache
- Orchestrator checks cache before running stage
- Can resume from any stage if previous stages cached
- Clear cache to force full re-run

---

## Implementation Status

**All 5 sessions complete! ✅**

### Files Created (20 total)

**Core Pipeline:**
- `orchestrator.py` - Main entry point
- `test_full_pipeline.py` - End-to-end tests

**Agents (5 files):**
- `agents/video_extractor.py` - Stage 1
- `agents/research_agent.py` - Stage 2
- `agents/debate_room.py` - Stage 3
- `agents/editor_agent.py` - Stage 4
- `agents/__init__.py`

**Tools (5 files):**
- `tools/youtube_downloader.py`
- `tools/consensus_scorer.py`
- `tools/token_tracker.py`
- `tools/ledger_updater.py`
- `tools/__init__.py`

**Tests (3 files):**
- `test_stage1.py`
- `test_stage2.py`
- `test_stage34.py`

**Configuration (6 files):**
- `claude.md` - Instruction ledger
- `.env.example` - API key template
- `.gitignore`
- `requirements.txt`
- `README.md`
- `QUICKSTART.md`

### Next Steps

1. **Set up environment:**
   ```bash
   cp .env.example .env
   # Add your API keys to .env
   pip install -r requirements.txt
   ```

2. **Run first pipeline:**
   ```bash
   python orchestrator.py --url "https://www.youtube.com/watch?v=VIDEO_ID"
   ```

3. **Review output:**
   - Check `outputs/report.md`
   - Review cache files in `cache/`
   - Provide feedback to improve future runs

4. **Iterate:**
   - Feedback saved to `claude.md`
   - Run again to see improvements
   - Customize style preferences in `claude.md`

---

## Phase 1-2: Enhanced Outputs & Multi-Round Debates ✅ COMPLETE

**Date:** 2026-04-26

### Goals
- Refactor debate system to run actual GROQ debates (not templates)
- Generate structured JSON outputs for visualization
- Separate visual insights from main extraction
- Enable knowledge graph and tree structure generation

### What Was Implemented

#### Phase 1: Multi-Round Debate System

**File Modified:** `agents/debate_room.py`

**Changes:**
- Replaced prompt templates with actual GROQ API calls
- Implemented multi-round debate loop (max 5 rounds)
- Skeptic vs Advocate debate positions
- Moderator identifies gaps between positions
- Continues until gaps resolved or max rounds reached
- Final synthesis generates editorial brief
- Saves to `outputs/debate_transcript.json`

**Key Features:**
- Round 1: Initial positions
- Rounds 2-5: Address identified gaps
- Uses GROQ llama-3.3-70b-versatile

#### Phase 2: Structured JSON Outputs

**New Files Created:**
1. `tools/knowledge_graph_builder.py` - Generates `outputs/graph.json`
   - Nodes: concepts, tools, claims
   - Edges: relationships between nodes
   - Metadata: counts and distributions

2. `tools/tree_builder.py` - Generates `outputs/tree.json`
   - Hierarchical tutorial structure
   - Sections → Key points → Concepts
   - Timestamp tracking

3. `verify_implementation.py` - Verification script
   - Checks all outputs exist
   - Validates structure of JSON files

**Files Modified:**
1. `agents/video_extractor.py` - Generates `outputs/visual_insights.json`
   - On-screen code snippets
   - Visual highlights with timestamps
   - UI elements and diagrams detected

2. `orchestrator.py` - Generates `outputs/report.json`
   - Metadata with verification score
   - Structured content sections
   - Verification statistics

### Output Files (6 total)

After running pipeline, `outputs/` contains:
1. `debate_transcript.json` - Multi-round debate
2. `graph.json` - Knowledge graph
3. `tree.json` - Hierarchical structure
4. `visual_insights.json` - Visual findings
5. `report.json` - Structured report
6. `report.md` - Clean markdown (existing)

### Testing

**Run verification:**
```bash
python verify_implementation.py
```

**Inspect outputs:**
```bash
cat outputs/debate_transcript.json | jq '.rounds_completed'
cat outputs/graph.json | jq '.metadata'
cat outputs/tree.json | jq '.metadata'
```

### Verification Checklist
- [x] Debate runs actual GROQ calls
- [x] Multi-round debate structure
- [x] All 5 JSON outputs generated
- [x] Knowledge graph has nodes + edges
- [x] Tree has hierarchical structure
- [x] Visual insights separated
- [x] Report includes verification score
- [x] Backward compatible

### Next Steps (Phase 3)
1. Terminal visualizations with Rich/Textual
2. Web dashboard with D3.js
3. Real-time pipeline progress
4. Interactive debate timeline

