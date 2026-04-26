"""
CWE (Common Weakness Enumeration) Database
Maps vulnerability types to CWE entries with mitigation advice.
"""

CWE_DATABASE = {
    "SQL_INJECTION": {
        "cwe_id": "CWE-89",
        "name": "Improper Neutralization of Special Elements used in an SQL Command",
        "severity": "CRITICAL",
        "description": "SQL injection occurs when untrusted data is sent to an interpreter as part of a command or query",
        "mitigation": "Use parameterized queries (prepared statements). Never concatenate user input into SQL strings.",
        "example_fix": "cursor.execute('SELECT * FROM users WHERE username=?', (username,))"
    },
    "XSS": {
        "cwe_id": "CWE-79",
        "name": "Improper Neutralization of Input During Web Page Generation",
        "severity": "HIGH",
        "description": "XSS allows attackers to inject malicious scripts into web pages viewed by other users",
        "mitigation": "Escape all user input before rendering in HTML. Use Content Security Policy headers.",
        "example_fix": "from markupsafe import escape; return f'<h1>Results for {escape(term)}</h1>'"
    },
    "PATH_TRAVERSAL": {
        "cwe_id": "CWE-22",
        "name": "Improper Limitation of a Pathname to a Restricted Directory",
        "severity": "HIGH",
        "description": "Path traversal allows attackers to access files outside the intended directory",
        "mitigation": "Validate and sanitize file paths. Use os.path.abspath() and check if path starts with allowed directory.",
        "example_fix": "safe_path = os.path.abspath(os.path.join(base_dir, filename)); if not safe_path.startswith(base_dir): raise ValueError()"
    },
    "COMMAND_INJECTION": {
        "cwe_id": "CWE-78",
        "name": "Improper Neutralization of Special Elements used in an OS Command",
        "severity": "CRITICAL",
        "description": "Command injection allows attackers to execute arbitrary system commands",
        "mitigation": "Never use shell=True with subprocess. Use argument lists instead of string commands. Validate all input.",
        "example_fix": "subprocess.run(['echo', user_input], shell=False, capture_output=True)"
    },
    "MISSING_INPUT_VALIDATION": {
        "cwe_id": "CWE-20",
        "name": "Improper Input Validation",
        "severity": "MEDIUM",
        "description": "Lack of input validation can lead to various injection attacks and unexpected behavior",
        "mitigation": "Validate all user input against expected format, length, and character set. Use allowlists, not denylists.",
        "example_fix": "if not re.match(r'^[a-zA-Z0-9_]+$', username): raise ValueError('Invalid username')"
    },
    "INSECURE_DESERIALIZATION": {
        "cwe_id": "CWE-502",
        "name": "Deserialization of Untrusted Data",
        "severity": "CRITICAL",
        "description": "Deserializing untrusted data can lead to remote code execution",
        "mitigation": "Never use pickle.loads() on untrusted data. Use JSON or other safe serialization formats.",
        "example_fix": "data = json.loads(user_input)  # Use JSON instead of pickle"
    },
    "WEAK_CRYPTO": {
        "cwe_id": "CWE-327",
        "name": "Use of a Broken or Risky Cryptographic Algorithm",
        "severity": "HIGH",
        "description": "Using weak cryptographic algorithms like MD5 or SHA1 for security purposes",
        "mitigation": "Use strong algorithms: SHA-256 or better for hashing, AES-256 for encryption.",
        "example_fix": "import hashlib; hash = hashlib.sha256(data.encode()).hexdigest()"
    }
}


def get_cwe_info(vuln_type: str) -> dict:
    """
    Get CWE information for a vulnerability type.
    
    Args:
        vuln_type: Vulnerability type (e.g., "SQL_INJECTION")
    
    Returns:
        CWE info dict or None if not found
    """
    return CWE_DATABASE.get(vuln_type)


def verify_against_cwe(vuln: dict) -> dict:
    """
    Verify vulnerability against CWE database and enrich with mitigation info.
    
    Args:
        vuln: Vulnerability dict
    
    Returns:
        Enriched vulnerability dict
    """
    vuln_type = vuln.get('type', 'UNKNOWN')
    cwe_info = get_cwe_info(vuln_type)
    
    if cwe_info:
        vuln['cwe_verified'] = True
        vuln['cwe_name'] = cwe_info['name']
        vuln['mitigation'] = cwe_info['mitigation']
        vuln['example_fix'] = cwe_info['example_fix']
    else:
        vuln['cwe_verified'] = False
        vuln['mitigation'] = "No specific mitigation available"
    
    return vuln
