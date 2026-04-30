const mysql = require('mysql');
const connection = mysql.createConnection({ ... });

function login(username, password) {
    const query = 'SELECT * FROM users WHERE username = ? AND password = ?';
    connection.query(query, [username, password], (err, results) => { {
        // ...
    });
}

function runCommand(cmd) {
    const { execFile } = require('child_process');
    execFile(cmd, [], (err, stdout, stderr) => { {
        // ...
    });
}
