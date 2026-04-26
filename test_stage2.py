#!/usr/bin/env python3
"""
Test Stage 2: Multi-Agent Security Analysis
Runs Stage 1 then Stage 2 to verify agent analysis works.
"""

import sys
import os
import subprocess
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.code_parser import run_stage1
from agents.security_agents import run_stage2


def create_test_file():
    """Create test file with SQL injection."""
    test_code = '''import sqlite3
from flask import request

def vulnerable_login(username, password):
    """SQL Injection vulnerability."""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    cursor.execute(query)
    return cursor.fetchone()
'''
    
    test_file = Path('test_vuln.py')
    test_file.write_text(test_code)
    print(f"✓ Created test file: {test_file}")
    return test_file


def stage_file(filepath):
    """Stage file for git."""
    try:
        subprocess.run(['git', 'add', str(filepath)], check=True, capture_output=True)
        print(f"✓ Staged file: {filepath}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to stage: {e}")
        return False


def unstage_file(filepath):
    """Unstage file."""
    try:
        subprocess.run(['git', 'reset', 'HEAD', str(filepath)], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        pass


def verify_results(results):
    """Verify Stage 2 results."""
    print("\n" + "=" * 50)
    print("VERIFICATION")
    print("=" * 50)

    if not results:
        print("✗ No results found")
        return False

    result = results[0]

    print(f"\n✓ File analyzed: {result['filepath']}")
    print(f"✓ Total vulnerabilities: {result['total_vulns']}")
    print(f"✓ High confidence: {result['high_confidence']}")
    print(f"✓ Medium confidence: {result['medium_confidence']}")

    # Check that at least one vuln was found
    assert result['total_vulns'] > 0, "Should find at least 1 vulnerability"

    # Display vulnerabilities
    for vuln in result['vulnerabilities']:
        print(f"\n  Vulnerability: {vuln['type']}")
        print(f"    Location: {vuln['location']}")
        print(f"    Severity: {vuln['severity']}")
        print(f"    Confidence: {vuln['confidence']} ({vuln['agent_count']} agents)")
        print(f"    Description: {vuln['description'][:80]}...")

    print("\n" + "=" * 50)
    print("✓ ALL VERIFICATIONS PASSED")
    print("=" * 50)

    return True


def main():
    """Run Stage 2 test."""
    print("=" * 50)
    print("STAGE 2 TEST: Multi-Agent Security Analysis")
    print("=" * 50)

    # Check for API keys
    from dotenv import load_dotenv
    load_dotenv()

    if not os.getenv('GEMINI_API_KEY'):
        print("✗ GEMINI_API_KEY not found in .env")
        print("  Copy .env.example to .env and add your API keys")
        return 1

    if not os.getenv('GROQ_API_KEY'):
        print("✗ GROQ_API_KEY not found in .env")
        print("  Copy .env.example to .env and add your API keys")
        return 1

    # Clean cache
    for cache_file in ['cache/stage1_extraction.json', 'cache/stage2_consensus.json']:
        cache_path = Path(cache_file)
        if cache_path.exists():
            cache_path.unlink()
            print(f"✓ Cleared {cache_file}")

    # Create test file
    test_file = create_test_file()

    try:
        # Stage file
        if not stage_file(test_file):
            print("✗ Failed to stage file")
            return 1

        # Run Stage 1
        print("\n" + "=" * 50)
        print("Running Stage 1...")
        extractions = run_stage1()

        if not extractions:
            print("✗ Stage 1 produced no extractions")
            return 1

        # Run Stage 2
        print("\n" + "=" * 50)
        print("Running Stage 2...")
        results = run_stage2(extractions)

        # Verify
        if verify_results(results):
            print("\n✓ Stage 2 test PASSED")
            return 0
        else:
            print("\n✗ Stage 2 test FAILED")
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
