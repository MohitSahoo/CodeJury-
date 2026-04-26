"""Ledger updater for claude.md instruction file."""

from pathlib import Path
from datetime import datetime, timedelta


class LedgerUpdater:
    """Update claude.md instruction ledger with feedback."""

    LEDGER_PATH = Path("claude.md")
    ARCHIVE_DAYS = 60

    def add_feedback(self, feedback: str):
        """
        Add timestamped feedback to ledger.

        Args:
            feedback: User feedback text
        """
        if not self.LEDGER_PATH.exists():
            raise FileNotFoundError(f"{self.LEDGER_PATH} not found")

        # Read current ledger
        with open(self.LEDGER_PATH) as f:
            content = f.read()

        # Parse sections
        sections = self._parse_sections(content)

        # Add feedback to Session Feedback Log
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        feedback_entry = f"\n### {timestamp}\n{feedback}\n"

        if "Session Feedback Log" in sections:
            sections["Session Feedback Log"] += feedback_entry
        else:
            sections["Session Feedback Log"] = feedback_entry

        # Archive old entries
        sections["Session Feedback Log"] = self._archive_old_entries(
            sections["Session Feedback Log"]
        )

        # Rebuild ledger
        new_content = self._rebuild_ledger(sections)

        # Write back
        with open(self.LEDGER_PATH, "w") as f:
            f.write(new_content)

    def _parse_sections(self, content: str) -> dict:
        """Parse ledger into sections."""
        sections = {}
        current_section = None
        current_content = []

        for line in content.split("\n"):
            if line.startswith("## "):
                # Save previous section
                if current_section:
                    sections[current_section] = "\n".join(current_content)

                # Start new section
                current_section = line[3:].strip()
                current_content = []
            else:
                current_content.append(line)

        # Save last section
        if current_section:
            sections[current_section] = "\n".join(current_content)

        return sections

    def _archive_old_entries(self, feedback_log: str) -> str:
        """Archive entries older than ARCHIVE_DAYS."""
        lines = feedback_log.split("\n")
        cutoff_date = datetime.now() - timedelta(days=self.ARCHIVE_DAYS)

        filtered_lines = []
        current_entry_date = None

        for line in lines:
            # Check if line is a timestamp header
            if line.startswith("### "):
                try:
                    date_str = line[4:14]  # Extract YYYY-MM-DD
                    entry_date = datetime.strptime(date_str, "%Y-%m-%d")
                    current_entry_date = entry_date
                except ValueError:
                    current_entry_date = None

            # Keep line if entry is recent or no date found
            if current_entry_date is None or current_entry_date >= cutoff_date:
                filtered_lines.append(line)

        return "\n".join(filtered_lines)

    def _rebuild_ledger(self, sections: dict) -> str:
        """Rebuild ledger from sections."""
        parts = [
            "# Agentic Newsroom — Instruction Ledger",
            f"_Last updated: {datetime.now().strftime('%Y-%m-%d')}_",
            "",
        ]

        # Add sections in order
        section_order = [
            "Output Style",
            "Consensus Settings",
            "Free Tier Guards",
            "Session Feedback Log",
        ]

        for section_name in section_order:
            if section_name in sections:
                parts.append(f"## {section_name}")
                parts.append(sections[section_name])
                parts.append("")

        return "\n".join(parts)


if __name__ == "__main__":
    # Test ledger updater
    updater = LedgerUpdater()
    updater.add_feedback("Test feedback: Pipeline completed successfully in 8 minutes.")
    print("✓ Feedback added to claude.md")
