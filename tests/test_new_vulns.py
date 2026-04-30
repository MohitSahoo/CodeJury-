"""
Test file with security vulnerabilities for pipeline validation.
"""
import os
import subprocess
import sqlite3

# SQL Injection vulnerability
def authenticate_user(username, password):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    cursor.execute(query)
    return cursor.fetchone()

# Command Injection vulnerability
def backup_file(filename):
    os.system(f"tar -czf backup.tar.gz {filename}")

# Path Traversal vulnerability
def read_user_file(filepath):
    with open(f"/var/data/{filepath}", 'r') as f:
        return f.read()

# Hardcoded credentials
API_KEY = "sk-1234567890abcdef"
DATABASE_PASSWORD = "admin123"

# Insecure subprocess call
def run_command(user_input):
    subprocess.call(f"echo {user_input}", shell=True)
# Re-test
