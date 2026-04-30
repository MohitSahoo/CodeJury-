import sqlite3

async def login_async(username, password):
    # SQL Injection in async function
    query = f"SELECT * FROM users WHERE username='{username}'"
    conn = sqlite3.connect('db.sqlite')
    cursor = conn.cursor()
    cursor.execute(query)
    return cursor.fetchone()

async def execute_cmd_async(cmd):
    # Command injection in async function
    import os
    os.system(cmd)
