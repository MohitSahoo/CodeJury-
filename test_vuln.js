const mysql = require('mysql');
const connection = mysql.createConnection({ ... });

function login(username, password) {
    // SQL Injection
    const query = `SELECT * FROM users WHERE username = '${username}' AND password = '${password}'`;
    connection.query(query, (err, results) => {
        // ...
    });
}

function runCommand(cmd) {
    // Command Injection
    const { exec } = require('child_process');
    exec(cmd, (err, stdout, stderr) => {
        // ...
    });
}
