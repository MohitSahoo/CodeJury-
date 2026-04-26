#!/usr/bin/env python3
"""
End-to-End Test: Full Security Audit Pipeline
Tests all 5 stages together.
"""

import sys
import os
import subprocess
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator import run_security_audit


def create_test_file():
    """Create test file with multiple vulnerabilities."""
    test_code = '''import sqlite3
import subprocess
from flask import request

def vulnerable_login(username, password):
    """SQL Injection vulnerability."""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    cursor.execute(query)
    return cursor.fetchone()

def vulnerable_command():
    """Command injection vulnerability."""
    user_input = request.args.get('cmd')
    result = subprocess.run(f'echo {user_input}', shell=True, capture_output=True)
    return result.stdout
'''
    
    test_file = Path('test_vuln.py')
    test_file.write_text(test_code)
    return test_file


def stage_file(filepath):
    try:
        subprocess.run(['git', 'add', str(filepath)], check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError:
        return False


def unstage_file(filepath):
    try:
        subprocess.run(['git', 'reset', 'HEAD', str(filepath)], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        pass


def main():
    print("=" * 50)
    print("END-TO-END TEST: Full Security Audit Pipeline")
    print("=" * 50)
    
    # Clear cache
    for cache_file in Path('cache').glob('stage*.json'):
        cache_file.unlink()
        print(f"✓ Cleared {cache_file}")
    
    test_file = create_test_file()
    print(f"✓ Created test file: {test_file}")
    
    try:
        if not stage_file(test_file):
            print("✗ Failed to stage file")
            return 1
        
        print(f"✓ Staged file: {test_file}")
        
        # Run full pipeline
        print("\n" + "=" * 50)
        print("Running full pipeline...")
        print("=" * 50)
        
        exit_code = run_security_audit()
        
        # Verify exit code
        print("\n" + "=" * 50)
        print("VERIFICATION")
        print("=" * 50)
        
        print(f"\nExit code: {exit_code}")
        
        # Should find vulnerabilities (exit code 0 or 1, not 2)
        assert exit_code in [0, 1], f"Expected exit code 0 or 1, got {exit_code}"
        
        # Check that cache files were created
        expected_caches = [
            'cache/stage1_extraction.json',
            'cache/stage2_consensus.json',
            'cache/stage3_debate.json',
            'cache/stage4_verified.json'
        ]
        
        for cache_file in expected_caches:
            cache_path = Path(cache_file)
            assert cache_path.exists(), f"Missing cache file: {cache_file}"
            print(f"✓ Cache file exists: {cache_file}")
        
        print("\n" + "=" * 50)
        print("✓ END-TO-END TEST PASSED")
        print("=" * 50)
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    finally:
        print("\n" + "=" * 50)
        print("CLEANUP")
        print("=" * 50)
        unstage_file(test_file)
        if test_file.exists():
            test_file.unlink()
            print(f"✓ Deleted test file: {test_file}")


if __name__ == "__main__":
    sys.exit(main())
