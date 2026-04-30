"""
Git diff extraction for security audit pipeline.
Extracts staged files and their diffs for analysis.
"""

import subprocess
from typing import List, Dict, Optional


def get_staged_files(extensions: List[str] = None) -> List[str]:
    """
    Get list of staged files with specified extensions.

    Args:
        extensions: List of file extensions (e.g., ['.py', '.js', '.java'])
                   If None, defaults to ['.py']

    Returns:
        List of file paths for staged files
    """
    if extensions is None:
        extensions = ['.py']

    try:
        result = subprocess.run(
            ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACMR'],
            capture_output=True,
            text=True,
            check=True
        )

        files = [
            f.strip()
            for f in result.stdout.split('\n')
            if f.strip() and any(f.strip().endswith(ext) for ext in extensions)
        ]

        return files

    except subprocess.CalledProcessError as e:
        print(f"Error getting staged files: {e}")
        return []


def get_staged_file_hashes(files: List[str]) -> Dict[str, str]:
    """
    Get git blob hashes for a list of staged files.

    Args:
        files: List of file paths

    Returns:
        Dict mapping filepath to its blob hash
    """
    hashes = {}
    for filepath in files:
        try:
            result = subprocess.run(
                ['git', 'rev-parse', f':{filepath}'],
                capture_output=True,
                text=True,
                check=True
            )
            hashes[filepath] = result.stdout.strip()
        except subprocess.CalledProcessError:
            hashes[filepath] = "unknown"
    return hashes


def get_staged_python_files() -> List[str]:
    """
    Get list of staged .py files (backward compatibility).

    Returns:
        List of file paths for staged Python files
    """
    return get_staged_files(['.py'])


def get_file_diff(filepath: str) -> str:
    """
    Get diff for specific file.

    Args:
        filepath: Path to file

    Returns:
        Diff content as string
    """
    try:
        result = subprocess.run(
            ['git', 'diff', '--cached', filepath],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout

    except subprocess.CalledProcessError as e:
        print(f"Error getting diff for {filepath}: {e}")
        return ""


def get_file_content(filepath: str) -> Optional[str]:
    """
    Read file content from disk.

    Args:
        filepath: Path to file

    Returns:
        File content as string, or None if error
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return None


def parse_diff_lines(diff_content: str) -> Dict[str, List[int]]:
    """
    Extract added and modified line numbers from diff.

    Args:
        diff_content: Git diff output

    Returns:
        Dict with 'added' and 'modified' line number lists
    """
    added_lines = []
    current_line = 0

    for line in diff_content.split('\n'):
        # Parse hunk headers like @@ -10,5 +10,7 @@
        if line.startswith('@@'):
            parts = line.split()
            if len(parts) >= 3:
                # Extract new file line number
                new_range = parts[2].lstrip('+').split(',')
                current_line = int(new_range[0])

        # Track added lines
        elif line.startswith('+') and not line.startswith('+++'):
            added_lines.append(current_line)
            current_line += 1

        # Track context lines (neither + nor -)
        elif not line.startswith('-'):
            current_line += 1

    return {
        'added': added_lines,
        'modified': added_lines  # For simplicity, treat all additions as modifications
    }


def is_git_repository() -> bool:
    """
    Check if current directory is a git repository.

    Returns:
        True if git repo, False otherwise
    """
    try:
        subprocess.run(
            ['git', 'rev-parse', '--git-dir'],
            capture_output=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError:
        return False
