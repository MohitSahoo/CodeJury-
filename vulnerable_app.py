import os
import pickle
import base64
from flask import Flask, request

app = Flask(__name__)

@app.route('/unpickle')
def unpickle():
    # Insecure Deserialization
    data = base64.b64decode(request.args.get('data'))
    obj = pickle.loads(data)
    return f"Unpickled {type(obj)}"

@app.route('/execute')
def execute():
    # Command Injection
    cmd = request.args.get('cmd')
    os.system(f"echo {cmd}")
    return "Executed"

@app.route('/query')
def query():
    # SQL Injection
    user_id = request.args.get('id')
    query = "SELECT * FROM users WHERE id = " + user_id
    # Simulating DB call
    return f"Executing {query}"

if __name__ == '__main__':
    app.run()

