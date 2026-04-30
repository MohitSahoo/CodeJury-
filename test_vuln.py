import sqlite3
import os

def login(username, password):
    # SQL Injection vulnerability
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute(query)
    return cursor.fetchone()

def run_command(cmd):
    # Command Injection vulnerability
    os.system(cmd)

# Test comment
# New change
