"""Stage 1: Video extraction using Gemini API."""

import os
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional
import google.generativeai as genai
from rich.console import Console

console = Console()


class VideoExtractor:
    """Extract structured content from YouTube videos using Gemini."""

    MAX_DURATION_SECONDS = 20 * 60  # 20 minutes
    CACHE_FILE = "cache/stage1_extraction.json"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize video extractor.

        Args:
            api_key: Gemini API key (defaults to GEMINI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")

        genai.configure(api_key=self.api_key)
        # Use Gemini 2.5 Flash for video analysis
        self.model = genai.GenerativeModel("gemini-2.5-flash")

    def extract(
        self,
        video_path: Path,
        transcript_path: Optional[Path],
        duration: float,
        force: bool = False,
    ) -> Dict[str, Any]:
        """
        Extract structured content from video.

        Args:
            video_path: Path to video file
            transcript_path: Path to transcript file (optional)
            duration: Video duration in seconds
            force: Force re-extraction even if cache exists

        Returns:
            Structured extraction as dict

        Raises:
            ValueError: If video exceeds duration limit
            RuntimeError: If extraction fails
        """
        # Check cache first
        cache_path = Path(self.CACHE_FILE)
        if cache_path.exists() and not force:
            console.print("✓ Using cached extraction", style="green")
            with open(cache_path) as f:
                return json.load(f)

        # Enforce duration limit
        if duration > self.MAX_DURATION_SECONDS:
            raise ValueError(
                f"Video duration ({duration/60:.1f} min) exceeds "
                f"{self.MAX_DURATION_SECONDS/60} min limit"
            )

        console.print(f"Analyzing video ({duration/60:.1f} min)...", style="cyan")

        # Upload video to Gemini
        video_file = genai.upload_file(str(video_path))
        console.print("✓ Video uploaded to Gemini", style="green")

        # Wait for file to become ACTIVE
        console.print("Waiting for video processing...", style="cyan")
        max_wait = 120  # 2 minutes max
        wait_time = 0
        while video_file.state.name != "ACTIVE":
            if wait_time >= max_wait:
                raise RuntimeError(f"Video processing timeout after {max_wait}s")
            time.sleep(2)
            wait_time += 2
            video_file = genai.get_file(video_file.name)
            if video_file.state.name == "FAILED":
                raise RuntimeError("Video processing failed")
        console.print("✓ Video ready for analysis", style="green")

        # Build prompt
        prompt = self._build_extraction_prompt(transcript_path)

        # Call Gemini API
        try:
            response = self.model.generate_content([video_file, prompt])
            extraction = self._parse_response(response.text)
        except Exception as e:
            raise RuntimeError(f"Gemini API call failed: {e}")
        finally:
            # Rate limit: 15 RPM for text
            time.sleep(4)

        # Save to cache
        cache_path.parent.mkdir(exist_ok=True)
        with open(cache_path, "w") as f:
            json.dump(extraction, f, indent=2)

        console.print(f"✓ Extraction saved to {cache_path}", style="green")

        # Extract and save visual insights separately
        self._save_visual_insights(extraction)

        return extraction

    def _build_extraction_prompt(self, transcript_path: Optional[Path]) -> str:
        """Build extraction prompt with optional transcript."""
        transcript_text = ""
        if transcript_path and transcript_path.exists():
            with open(transcript_path) as f:
                transcript_text = f"\n\nTranscript:\n{f.read()}"

        return f"""Analyze this technical tutorial video and extract structured information.
{transcript_text}

Return ONLY valid JSON (no markdown fences) with this exact structure:
{{
  "title": "Video title",
  "summary": "2-3 sentence summary of what the tutorial teaches",
  "steps": [
    {{
      "timestamp": "MM:SS",
      "description": "What happens in this step",
      "key_points": ["point 1", "point 2"]
    }}
  ],
  "code_shown": [
    {{
      "language": "python",
      "snippet": "code snippet",
      "explanation": "what this code does"
    }}
  ],
  "tools_used": ["tool1", "tool2"],
  "prerequisites": ["prerequisite1", "prerequisite2"],
  "key_concepts": ["concept1", "concept2"]
}}

Focus on technical accuracy. Include timestamps for major steps."""

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Gemini response into structured dict."""
        # Remove markdown fences if present
        text = response_text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1])

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse Gemini response as JSON: {e}\n{text}")

    def _save_visual_insights(self, extraction: Dict[str, Any]) -> None:
        """Extract and save visual-specific insights separately."""
        visual_insights = {
            "on_screen_code": extraction.get("code_shown", []),
            "visual_highlights": [],
            "ui_elements_detected": [],
            "diagrams_detected": [],
            "frame_analysis": {
                "total_steps": len(extraction.get("steps", [])),
                "code_snippets_shown": len(extraction.get("code_shown", [])),
            }
        }

        # Extract visual highlights from steps
        for step in extraction.get("steps", []):
            if step.get("timestamp"):
                visual_insights["visual_highlights"].append({
                    "timestamp": step.get("timestamp"),
                    "description": step.get("description", ""),
                    "key_points": step.get("key_points", [])
                })

        # Detect UI elements (simple heuristic based on keywords)
        for step in extraction.get("steps", []):
            desc_lower = step.get("description", "").lower()
            if any(keyword in desc_lower for keyword in ["button", "menu", "click", "interface", "ui", "screen"]):
                visual_insights["ui_elements_detected"].append({
                    "timestamp": step.get("timestamp", ""),
                    "element": step.get("description", "")
                })

        # Detect diagrams (simple heuristic)
        for step in extraction.get("steps", []):
            desc_lower = step.get("description", "").lower()
            if any(keyword in desc_lower for keyword in ["diagram", "chart", "graph", "architecture", "flow"]):
                visual_insights["diagrams_detected"].append({
                    "timestamp": step.get("timestamp", ""),
                    "type": step.get("description", "")
                })

        # Save to outputs
        output_path = Path("outputs/visual_insights.json")
        output_path.parent.mkdir(exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(visual_insights, f, indent=2)

        console.print(f"✓ Visual insights: {output_path}", style="green")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    # Test extraction
    extractor = VideoExtractor()
    result = extractor.extract(
        video_path=Path("cache/video.mp4"),
        transcript_path=Path("cache/transcript.txt"),
        duration=212.0,  # 3.5 min
    )

    print(json.dumps(result, indent=2))
