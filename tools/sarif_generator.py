import json
import os
from datetime import datetime
from typing import List, Dict, Any

def generate_sarif(verified_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generates a SARIF (Static Analysis Results Interchange Format) v2.1.0 report.
    """
    sarif = {
        "$schema": "https://schemastore.azurewebsites.net/schemas/json/sarif-2.1.0-rtm.5.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "Security Audit Pipeline",
                        "version": "1.2.0",
                        "informationUri": "https://github.com/MohitSahoo/CodeJury-",
                        "rules": []
                    }
                },
                "results": []
            }
        ]
    }

    rules = {}
    results = []

    for file_result in verified_results:
        filepath = file_result.get('filepath', 'unknown')
        for vuln in file_result.get('vulnerabilities', []):
            rule_id = vuln.get('type', 'GENERIC_VULNERABILITY')
            
            # Register rule if new
            if rule_id not in rules:
                rules[rule_id] = {
                    "id": rule_id,
                    "shortDescription": {
                        "text": vuln.get('type', 'Vulnerability detected')
                    },
                    "helpUri": f"https://cwe.mitre.org/data/definitions/{vuln.get('cwe_id', '0').replace('CWE-', '')}.html"
                }

            # Create result entry
            try:
                line_str = vuln.get('location', '0').split(':')[-1]
                line_no = int(line_str) if line_str.isdigit() else 1
            except:
                line_no = 1

            result = {
                "ruleId": rule_id,
                "message": {
                    "text": vuln.get('description', 'No description provided')
                },
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {
                                "uri": filepath
                            },
                            "region": {
                                "startLine": line_no
                            }
                        }
                    }
                ],
                "properties": {
                    "severity": vuln.get('severity', 'MEDIUM'),
                    "confidence": vuln.get('confidence', 'MEDIUM'),
                    "cwe": vuln.get('cwe_id', 'N/A')
                }
            }
            results.append(result)

    sarif["runs"][0]["tool"]["driver"]["rules"] = list(rules.values())
    sarif["runs"][0]["results"] = results

    return sarif

def save_sarif(verified_results: List[Dict[str, Any]], output_path: str = "security-results.sarif"):
    """
    Generates and saves the SARIF report to a file.
    """
    sarif_data = generate_sarif(verified_results)
    with open(output_path, 'w') as f:
        json.dump(sarif_data, f, indent=2)
    return output_path
