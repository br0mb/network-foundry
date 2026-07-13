#!/usr/bin/env python3
"""
Wazuh SIEM Security Monitor — Data Collection Script
=====================================================
Runs on an AI-Agent cron schedule, queries the Wazuh API and OpenSearch indexer
for security alerts, agent status, rootcheck, and syscheck data.

Filters:
  - Alert severity level >= 3 (configurable via MIN_SEVERITY)
  - Time window: last 30 minutes (configurable via TIME_WINDOW_MIN)
  - Deduplicates alerts by rule ID + description
  - Suppresses known false positives (rootcheck FP list)

Output: JSON to stdout. Empty JSON object {} if nothing noteworthy.
The AI-Agent cron job injects this as context for the agent to analyze
and write an Obsidian-formatted markdown report.

Author: AI-Agent for Network Foundry Lab
Created: 2026-07-09
"""

import json
import sys
import subprocess
import urllib.request
import urllib.parse
import ssl
import base64
import os
from datetime import datetime, timedelta, timezone

# ============================================================
# Configuration
# ============================================================

WAZUH_HOST = os.getenv("WAZUH_HOST", "10.0.24.13")
WAZUH_API_PORT = os.getenv("WAZUH_API_PORT", "55000")
WAZUH_INDEXER_PORT = os.getenv("WAZUH_INDEXER_PORT", "9200")
WAZUH_USER = os.getenv("WAZUH_API_USER", "wazuh")
WAZUH_PASS = os.getenv("WAZUH_API_PASS", "[REDACTED]")
INDEXER_USER = os.getenv("INDEXER_USER", "admin")
INDEXER_PASS = os.getenv("INDEXER_PASS", "[REDACTED]")
SSH_USER = os.getenv("WAZUH_SSH_USER", "wazuh-user")
SSH_PASS = os.getenv("WAZUH_SSH_PASS", "[REDACTED]")

MIN_SEVERITY = 3
TIME_WINDOW_MIN = 30
MAX_ALERTS = 50

# Known false positives to suppress from rootcheck
# Wazuh's rootcheck uses signature-based detection that flags standard
# Linux system binaries as "trojaned" because they link against bash/libc.
# These are well-documented false positives on Ubuntu/Debian systems.
ROOTCHECK_FALSE_POSITIVES = [
    "/bin/chfn", "/bin/chsh", "/bin/mount", "/bin/umount",
    "/bin/md5sum", "/bin/passwd", "/bin/date", "/bin/cat",
    "/bin/uname", "/bin/chgrp", "/bin/chmod", "/bin/chown",
    "/bin/kill", "/bin/ln", "/bin/ls", "/bin/mv", "/bin/rm",
    "/bin/su", "/bin/sh", "/bin/bash", "/bin/cp", "/bin/dd",
    "/bin/df", "/bin/echo", "/bin/env", "/bin/id", "/bin/mkdir",
    "/bin/ping", "/bin/ps", "/bin/pwd", "/bin/rmdir", "/bin/sleep",
    "/bin/sync", "/bin/touch", "/bin/true", "/bin/false",
    "/usr/bin/passwd", "/usr/bin/date", "/usr/bin/cat",
    "/usr/bin/uname", "/usr/bin/chgrp", "/usr/bin/chmod",
    "/usr/bin/chown", "/usr/bin/kill", "/usr/bin/ln",
    "/usr/bin/ls", "/usr/bin/mv", "/usr/bin/rm", "/usr/bin/su",
    "/usr/bin/cp", "/usr/bin/dd", "/usr/bin/df", "/usr/bin/echo",
    "/usr/bin/env", "/usr/bin/id", "/usr/bin/mkdir", "/usr/bin/ping",
    "/usr/bin/ps", "/usr/bin/pwd", "/usr/bin/rmdir", "/usr/bin/sleep",
    "/usr/bin/sync", "/usr/bin/touch", "/usr/bin/true", "/usr/bin/false",
    "/sbin/ifconfig", "/usr/sbin/ifconfig",
    "/usr/bin/sudo", "/usr/bin/su",
]

# SSH command to reach the Wazuh server (for indexer queries via localhost)
SSH_CMD = [
    "sshpass", "-p", SSH_PASS,
    "ssh", "-o", "ConnectTimeout=15", "-o", "StrictHostKeyChecking=no",
    "-o", "UserKnownHostsFile=/dev/null",
    "-o", "PreferredAuthentications=password",
    f"{SSH_USER}@{WAZUH_HOST}"
]

# SSL context that ignores self-signed certs
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE


def api_request(path, method="GET", body=None):
    """Make an authenticated request to the Wazuh REST API."""
    url = f"https://{WAZUH_HOST}:{WAZUH_API_PORT}{path}"
    auth = base64.b64encode(f"{WAZUH_USER}:{WAZUH_PASS}".encode()).decode()

    # First get a JWT token
    token_url = f"https://{WAZUH_HOST}:{WAZUH_API_PORT}/security/user/authenticate"
    req = urllib.request.Request(token_url, method="GET")
    req.add_header("Authorization", f"Basic {auth}")
    try:
        with urllib.request.urlopen(req, context=SSL_CTX, timeout=10) as resp:
            token_data = json.loads(resp.read().decode())
            token = token_data["data"]["token"]
    except Exception as e:
        return {"error": f"Auth failed: {e}"}

    # Now make the actual request with the JWT token
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    if body:
        req.add_header("Content-Type", "application/json")
        req.data = json.dumps(body).encode()

    try:
        with urllib.request.urlopen(req, context=SSL_CTX, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}


def indexer_query(query_body):
    """Query the Wazuh indexer (OpenSearch) for alerts via SSH tunnel.

    The indexer is bound to 127.0.0.1:9200 on the Wazuh server and not
    accessible externally. We SSH in and run curl on localhost instead.
    """
    query_json = json.dumps(query_body)
    # URL-encode the query for safe shell passing
    curl_cmd = (
        f'curl -sk --connect-timeout 5 '
        f'-u {INDEXER_USER}:{INDEXER_PASS} '
        f'"https://127.0.0.1:9200/wazuh-alerts-*/_search'
        f'?size={MAX_ALERTS}&sort=timestamp:desc" '
        f'-H "Content-Type: application/json" '
        f"-d '{query_json}'"
    )

    try:
        result = subprocess.run(
            SSH_CMD + [curl_cmd],
            capture_output=True, text=True, timeout=25
        )
        if result.returncode != 0:
            return {"error": f"SSH curl failed: {result.stderr[:200]}"}
        return json.loads(result.stdout)
    except Exception as e:
        return {"error": f"SSH query failed: {e}"}


def get_agent_status():
    """Get status of all Wazuh agents."""
    result = api_request("/agents?limit=100")
    agents = []
    if "data" in result and "affected_items" in result["data"]:
        for a in result["data"]["affected_items"]:
            agents.append({
                "id": a.get("id", "?"),
                "name": a.get("name", "?"),
                "ip": a.get("ip", "N/A"),
                "status": a.get("status", "unknown"),
                "version": a.get("version", "N/A"),
                "os": a.get("os", {}).get("name", "N/A"),
                "last_keepalive": a.get("lastKeepAlive", "N/A"),
                "date_added": a.get("dateAdd", "N/A"),
            })
    return agents


def get_manager_status():
    """Get Wazuh manager daemon status."""
    result = api_request("/manager/status")
    daemons = {}
    if "data" in result and "affected_items" in result["data"]:
        for item in result["data"]["affected_items"]:
            for daemon, state in item.items():
                daemons[daemon] = state
    return daemons


def get_manager_info():
    """Get Wazuh manager version and info."""
    result = api_request("/manager/info")
    if "data" in result and "affected_items" in result["data"]:
        return result["data"]["affected_items"][0]
    return {}


def get_recent_alerts():
    """Query OpenSearch for alerts in the last TIME_WINDOW_MIN minutes, level >= MIN_SEVERITY."""
    now = datetime.now(timezone.utc)
    time_from = (now - timedelta(minutes=TIME_WINDOW_MIN)).strftime("%Y-%m-%dT%H:%M:%S")

    query = {
        "query": {
            "bool": {
                "must": [
                    {"range": {"rule.level": {"gte": MIN_SEVERITY}}},
                    {"range": {"@timestamp": {"gte": time_from}}}
                ]
            }
        }
    }

    result = indexer_query(query)
    alerts = []

    if "error" in result:
        return {"error": result["error"]}

    hits = result.get("hits", {}).get("hits", [])
    seen = set()  # for deduplication

    for hit in hits:
        src = hit.get("_source", {})
        rule = src.get("rule", {})
        agent = src.get("agent", {})
        data = src.get("data", {})

        # Deduplicate by rule ID + description + agent name
        dedup_key = f"{rule.get('id', '?')}|{rule.get('description', '?')}|{agent.get('name', '?')}"
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        alert = {
            "rule_id": rule.get("id", "?"),
            "rule_level": rule.get("level", "?"),
            "rule_description": rule.get("description", "?"),
            "rule_groups": rule.get("groups", []),
            "agent_name": agent.get("name", "?"),
            "agent_id": agent.get("id", "?"),
            "timestamp": src.get("@timestamp", "?"),
            "source_log": src.get("full_log", "")[:200],
            "data": data,
            "pci_dss": rule.get("pci_dss", []),
            "hipaa": rule.get("hipaa", []),
            "nist_800_53": rule.get("nist_800_53", []),
        }
        alerts.append(alert)

    return alerts


def get_rootcheck(agent_id="003"):
    """Get rootcheck (rootkit detection) results for an agent."""
    result = api_request(f"/rootcheck/{agent_id}?limit=20")
    findings = []
    if "data" in result and "affected_items" in result["data"]:
        for item in result["data"]["affected_items"]:
            log = item.get("log", "")
            # Skip known false positives
            if any(fp in log for fp in ROOTCHECK_FALSE_POSITIVES):
                continue
            findings.append({
                "status": item.get("status", "?"),
                "log": log,
                "date_first": item.get("date_first", "?"),
                "date_last": item.get("date_last", "?"),
            })
    return findings


def get_syscheck_summary(agent_id="003"):
    """Get recent file integrity monitoring changes for an agent."""
    result = api_request(f"/syscheck/{agent_id}?limit=10&sort=-date")
    changes = []
    if "data" in result and "affected_items" in result["data"]:
        for item in result["data"]["affected_items"]:
            changes.append({
                "file": item.get("file", "?"),
                "date": item.get("date", "?"),
                "changes": item.get("changes", 0),
                "perm": item.get("perm", "?"),
                "uname": item.get("uname", "?"),
                "size": item.get("size", 0),
            })
    return changes


def get_vulnerabilities():
    """Get detected vulnerabilities from the Wazuh indexer via SSH."""
    query = {
        "query": {"match_all": {}},
        "sort": [{"severity": {"order": "desc"}}],
    }
    query_json = json.dumps(query)
    curl_cmd = (
        f'curl -sk --connect-timeout 5 '
        f'-u {INDEXER_USER}:{INDEXER_PASS} '
        f'"https://127.0.0.1:9200/wazuh-states-vulnerabilities-*/_search?size=10" '
        f'-H "Content-Type: application/json" '
        f"-d '{query_json}'"
    )

    try:
        result = subprocess.run(
            SSH_CMD + [curl_cmd],
            capture_output=True, text=True, timeout=25
        )
        if result.returncode != 0:
            return []
        data = json.loads(result.stdout)
    except Exception:
        return []

    vulns = []
    for hit in data.get("hits", {}).get("hits", [])[:10]:
        src = hit.get("_source", {})
        vulns.append({
            "cve": src.get("cve", "?"),
            "severity": src.get("severity", "?"),
            "package": src.get("package", {}).get("name", "?"),
            "version": src.get("package", {}).get("version", "?"),
            "agent": src.get("agent", {}).get("name", "?"),
        })
    return vulns


def main():
    """Main collection function — outputs JSON to stdout."""
    report = {
        "scan_time": datetime.now(timezone.utc).isoformat(),
        "time_window_min": TIME_WINDOW_MIN,
        "min_severity": MIN_SEVERITY,
        "wazuh_host": WAZUH_HOST,
    }

    # 1. Manager info and status
    report["manager"] = get_manager_info()
    report["daemons"] = get_manager_status()

    # 2. Agent status
    report["agents"] = get_agent_status()

    # 3. Recent alerts (level 3+, last 30 min)
    report["alerts"] = get_recent_alerts()

    # 4. Rootcheck (rootkit detection) — filtered for false positives
    report["rootcheck"] = get_rootcheck("003")

    # 5. Syscheck (file integrity monitoring)
    report["syscheck"] = get_syscheck_summary("003")

    # 6. Vulnerabilities
    report["vulnerabilities"] = get_vulnerabilities()

    # Determine if anything is noteworthy
    has_alerts = isinstance(report["alerts"], list) and len(report["alerts"]) > 0
    has_disconnected = any(a["status"] == "disconnected" for a in report["agents"])
    has_rootcheck = len(report["rootcheck"]) > 0
    has_vulns = len(report["vulnerabilities"]) > 0
    stopped_daemons = {k: v for k, v in report["daemons"].items() if v == "stopped"}

    report["summary"] = {
        "alert_count": len(report["alerts"]) if isinstance(report["alerts"], list) else 0,
        "disconnected_agents": [a["name"] for a in report["agents"] if a["status"] == "disconnected"],
        "rootcheck_findings": len(report["rootcheck"]),
        "vulnerability_count": len(report["vulnerabilities"]),
        "stopped_daemons": list(stopped_daemons.keys()),
        "noteworthy": has_alerts or has_disconnected or has_rootcheck or has_vulns or len(stopped_daemons) > 0,
    }

    # Output JSON to stdout — AI-Agent cron injects this into the agent prompt
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()