"""
Test file with multiple known vulnerabilities for false negative testing.
"""
import sqlite3
import subprocess
import pickle
from flask import Flask, request

app = Flask(__name__)

# VULN 1: SQL Injection (f-string)
def get_user_by_name(username):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    query = f"SELECT * FROM users WHERE username = '{username}'"
    cursor.execute(query)
    return cursor.fetchone()

# VULN 2: SQL Injection (.format())
def get_user_by_id(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    query = "SELECT * FROM users WHERE id = {}".format(user_id)
    cursor.execute(query)
    return cursor.fetchone()

# VULN 3: Command Injection (shell=True with user input)
@app.route('/ping')
def ping_host():
    host = request.args.get('host')
    result = subprocess.run(f"ping -c 1 {host}", shell=True, capture_output=True)
    return result.stdout

# VULN 4: Path Traversal (user input in file path)
@app.route('/read')
def read_file():
    filename = request.args.get('file')
    with open(f"/var/data/{filename}", 'r') as f:
        return f.read()

# VULN 5: Insecure Deserialization
@app.route('/load')
def load_data():
    data = request.data
    obj = pickle.loads(data)
    return str(obj)

# VULN 6: XSS (unescaped user input in template)
@app.route('/greet')
def greet():
    name = request.args.get('name')
    return f"<h1>Hello {name}!</h1>"

# VULN 7: Command Injection (subprocess with user input, no shell)
@app.route('/run')
def run_command():
    cmd = request.args.get('cmd')
    result = subprocess.run([cmd], capture_output=True)
    return result.stdout
