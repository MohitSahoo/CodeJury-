#!/usr/bin/env python3
"""
Test Stage 1: Code Parsing & AST Analysis
Creates a vulnerable test file and runs Stage 1 parser.
"""

import sys
import os
import subprocess
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.code_parser import run_stage1


def create_test_file():
    """Create a test file with multiple vulnerabilities."""
    test_code = '''"""
Test file with multiple security vulnerabilities.
DO NOT use in production!
"""

import sqlite3
import subprocess
from flask import request


def vulnerable_login(username, password):
    """SQL Injection vulnerability - uses f-string in query."""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # VULN: SQL Injection via f-string
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    cursor.execute(query)

    return cursor.fetchone()


def vulnerable_search():
    """XSS vulnerability - unescaped user input in HTML."""
    search_term = request.args.get('q')

    # VULN: XSS - user input directly in HTML
    return f"<h1>Results for {search_term}</h1>"


def vulnerable_file_read():
    """Path traversal vulnerability."""
    filename = request.args.get('file')

    # VULN: Path traversal - user controls file path
    with open(f'/var/data/{filename}', 'r') as f:
        return f.read()


def vulnerable_command():
    """Command injection vulnerability."""
    user_input = request.args.get('cmd')

    # VULN: Command injection with shell=True
    result = subprocess.run(f'echo {user_input}', shell=True, capture_output=True)
    return result.stdout


def safe_function():
    """This function has no vulnerabilities."""
    return "Hello, World!"
'''

    test_file = Path('test_vuln.py')
    test_file.write_text(test_code)
    print(f"✓ Created test file: {test_file}")
    return test_file


def stage_file(filepath):
    """Stage file for git commit."""
    try:
        subprocess.run(['git', 'add', str(filepath)], check=True, capture_output=True)
        print(f"✓ Staged file: {filepath}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to stage file: {e}")
        return False


def unstage_file(filepath):
    """Unstage file."""
    try:
        subprocess.run(['git', 'reset', 'HEAD', str(filepath)], check=True, capture_output=True)
        print(f"✓ Unstaged file: {filepath}")
    except subprocess.CalledProcessError:
        pass


def verify_extraction(extractions):
    """Verify extraction results."""
    print("\n" + "=" * 50)
    print("VERIFICATION")
    print("=" * 50)

    if not extractions:
        print("✗ No extractions found")
        return False

    extraction = extractions[0]

    # Check basic structure
    assert extraction['parseable'], "File should be parseable"
    assert extraction['has_security_patterns'], "Should detect security patterns"

    # Check SQL patterns
    sql_count = len(extraction['sql_patterns'])
    print(f"\n✓ SQL patterns detected: {sql_count}")
    assert sql_count >= 1, "Should detect at least 1 SQL pattern"

    for sql in extraction['sql_patterns']:
        print(f"  - Line {sql['lineno']}: {sql['query_snippet'][:50]}... (Risk: {sql['risk']})")

    # Check user inputs
    input_count = len(extraction['user_inputs'])
    print(f"\n✓ User inputs detected: {input_count}")
    assert input_count >= 4, "Should detect at least 4 user inputs"

    for inp in extraction['user_inputs']:
        print(f"  - Line {inp['lineno']}: {inp['source']} (Type: {inp['type']})")

    # Check file operations
    file_ops_count = len(extraction['file_operations'])
    print(f"\n✓ File operations detected: {file_ops_count}")
    assert file_ops_count >= 1, "Should detect at least 1 file operation"

    for op in extraction['file_operations']:
        print(f"  - Line {op['lineno']}: {op['operation']} (Risk: {op['risk']})")

    # Check subprocess calls
    subprocess_count = len(extraction['subprocess_calls'])
    print(f"\n✓ Subprocess calls detected: {subprocess_count}")
    assert subprocess_count >= 1, "Should detect at least 1 subprocess call"

    for call in extraction['subprocess_calls']:
        print(f"  - Line {call['lineno']}: {call['function']} (Risk: {call['risk']})")

    # Check functions
    func_count = len(extraction['functions'])
    print(f"\n✓ Functions extracted: {func_count}")
    assert func_count >= 5, "Should extract at least 5 functions"

    for func in extraction['functions']:
        print(f"  - {func['name']}() at line {func['lineno']}")

    print("\n" + "=" * 50)
    print("✓ ALL VERIFICATIONS PASSED")
    print("=" * 50)

    return True


def main():
    """Run Stage 1 test."""
    print("=" * 50)
    print("STAGE 1 TEST: Code Parsing & AST Analysis")
    print("=" * 50)

    # Clean up any existing cache
    cache_file = Path('cache/stage1_extraction.json')
    if cache_file.exists():
        cache_file.unlink()
        print("✓ Cleared existing cache")

    # Create test file
    test_file = create_test_file()

    try:
        # Stage file
        if not stage_file(test_file):
            print("✗ Failed to stage file - is this a git repository?")
            return 1

        # Run Stage 1
        print("\n" + "=" * 50)
        extractions = run_stage1()

        # Verify results
        if verify_extraction(extractions):
            print("\n✓ Stage 1 test PASSED")
            return 0
        else:
            print("\n✗ Stage 1 test FAILED")
            return 1

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        # Cleanup
        print("\n" + "=" * 50)
        print("CLEANUP")
        print("=" * 50)
        unstage_file(test_file)
        if test_file.exists():
            test_file.unlink()
            print(f"✓ Deleted test file: {test_file}")


if __name__ == "__main__":
    sys.exit(main())
