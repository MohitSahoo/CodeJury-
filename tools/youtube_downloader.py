"""YouTube video downloader using yt-dlp."""

import os
import subprocess
from pathlib import Path
from typing import Tuple, Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


class YouTubeDownloader:
    """Download YouTube videos and transcripts using yt-dlp."""

    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def download(self, url: str) -> Tuple[Path, Optional[Path], float]:
        """
        Download video and transcript from YouTube.

        Args:
            url: YouTube video URL

        Returns:
            Tuple of (video_path, transcript_path, duration_seconds)

        Raises:
            RuntimeError: If download fails
        """
        video_path = self.cache_dir / "video.mp4"
        transcript_path = self.cache_dir / "transcript.txt"

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Get video info first
            progress.add_task(description="Fetching video info...", total=None)
            duration = self._get_duration(url)

            # Download video
            progress.add_task(description="Downloading video...", total=None)
            self._download_video(url, video_path)

            # Download transcript
            progress.add_task(description="Downloading transcript...", total=None)
            transcript_exists = self._download_transcript(url, transcript_path)

        console.print(f"✓ Downloaded video: {video_path}", style="green")
        if transcript_exists:
            console.print(f"✓ Downloaded transcript: {transcript_path}", style="green")
        else:
            console.print("⚠ No transcript available", style="yellow")
            transcript_path = None

        return video_path, transcript_path, duration

    def _get_duration(self, url: str) -> float:
        """Get video duration in seconds."""
        try:
            result = subprocess.run(
                ["yt-dlp", "--print", "duration", url],
                capture_output=True,
                text=True,
                check=True,
            )
            return float(result.stdout.strip())
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to get video duration: {e.stderr}")
        except ValueError:
            raise RuntimeError("Invalid duration format")

    def _download_video(self, url: str, output_path: Path) -> None:
        """Download video file."""
        try:
            subprocess.run(
                [
                    "yt-dlp",
                    "-f", "best[ext=mp4]",
                    "-o", str(output_path),
                    url,
                ],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to download video: {e.stderr.decode()}")

    def _download_transcript(self, url: str, output_path: Path) -> bool:
        """
        Download transcript/subtitles if available.

        Returns:
            True if transcript was downloaded, False otherwise
        """
        try:
            subprocess.run(
                [
                    "yt-dlp",
                    "--write-auto-sub",
                    "--sub-lang", "en",
                    "--skip-download",
                    "--convert-subs", "txt",
                    "-o", str(output_path.with_suffix("")),
                    url,
                ],
                check=True,
                capture_output=True,
            )
            # yt-dlp adds .en.txt suffix
            generated_file = output_path.parent / f"{output_path.stem}.en.txt"
            if generated_file.exists():
                generated_file.rename(output_path)
                return True
            return False
        except subprocess.CalledProcessError:
            return False


if __name__ == "__main__":
    # Test with a sample video
    downloader = YouTubeDownloader()
    video, transcript, duration = downloader.download(
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    )
    print(f"Duration: {duration:.1f}s ({duration/60:.1f} min)")
