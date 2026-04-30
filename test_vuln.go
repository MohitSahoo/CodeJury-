package main

import (
	"database/sql"
	"fmt"
	"os/exec"
)

func login(db *sql.DB, username, password string) {
	// SQL Injection
	query := fmt.Sprintf("SELECT * FROM users WHERE username = '%s' AND password = '%s'", username, password)
	db.Query(query)
}

func runCommand(cmd string) {
	// Command Injection
	exec.Command("sh", "-c", cmd).Run()
}
