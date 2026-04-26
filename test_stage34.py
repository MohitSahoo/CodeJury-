#!/usr/bin/env python3
"""
Test Stages 3-4: Debate & Verification
Runs full pipeline through Stage 4.
"""

import sys
import os
import subprocess
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.code_parser import run_stage1
from agents.security_agents import run_stage2
from agents.debate_room import run_stage3
from agents.verifier import run_stage4


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
    print("STAGES 3-4 TEST: Debate & Verification")
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
        
        # Run Stages 1-4
        print("\n" + "=" * 50)
        extractions = run_stage1()
        consensus = run_stage2(extractions)
        debate = run_stage3(consensus)
        verified = run_stage4(debate, consensus)
        
        # Verify results
        print("\n" + "=" * 50)
        print("VERIFICATION")
        print("=" * 50)
        
        total_vulns = sum(r['total_vulns'] for r in verified)
        print(f"\n✓ Total verified vulnerabilities: {total_vulns}")
        
        assert total_vulns > 0, "Should find at least 1 vulnerability"
        
        for result in verified:
            print(f"\nFile: {result['filepath']}")
            print(f"  Vulnerabilities: {result['total_vulns']}")
            
            for vuln in result['vulnerabilities']:
                print(f"\n  {vuln['type']}:")
                print(f"    Location: {vuln['location']}")
                print(f"    Severity: {vuln['debated_severity']}")
                print(f"    CWE: {vuln.get('cwe_id', 'N/A')}")
                print(f"    Verified: {vuln.get('cwe_verified', False)}")
                
                if vuln.get('mitigation'):
                    print(f"    Mitigation: {vuln['mitigation'][:60]}...")
            
            if result.get('attack_tree'):
                tree = result['attack_tree']
                print(f"\n  Attack Tree:")
                print(f"    Root goal: {tree['root_goal']}")
                print(f"    Attack paths: {tree['total_paths']}")
                print(f"    Highest severity: {tree['highest_severity']}")
        
        print("\n" + "=" * 50)
        print("✓ ALL TESTS PASSED")
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
