#!/usr/bin/env python3
"""
Network Foundry Network Monitor — Data Collection Script
================================================
Runs on an AI-Agent cron schedule, SSHes into R1 (Cisco 2650XM) and SW-1
(Cisco 3750) to collect network health data. Also pings key infrastructure
devices for reachability.

Collects:
  - Device reachability (ping sweep)
  - R1 interface status (show ip interface brief)
  - R1 CPU utilization (show processes cpu)
  - R1 routing table summary (show ip route summary)
  - R1 interface error counters (show interfaces)
  - R1 OSPF neighbor status (show ip ospf neighbor)
  - R1 DHCP pool info (show ip dhcp pool)
  - SW-1 interface status (show ip interface brief)
  - SW-1 interface error counters (show interfaces)

Output: JSON to stdout. Injected into the agent's prompt for analysis.
The agent writes an Obsidian-formatted NOC report with Tier 1/2 learning context.

Author: AI-Agent for Network Foundry Lab
Created: 2026-07-09
"""

import json
import sys
import subprocess
import re
import os
from datetime import datetime, timezone

# ============================================================
# Configuration
# ============================================================

R1_HOST = os.getenv("R1_HOST", "10.0.24.1")
R1_USER = os.getenv("R1_USER", "admin")
R1_PASS = os.getenv("R1_PASS", "[REDACTED]")

SW1_HOST = os.getenv("SW1_HOST", "10.0.24.11")
SW1_USER = os.getenv("SW1_USER", "admin")
SW1_PASS = os.getenv("SW1_PASS", "[REDACTED]")

# Devices to ping-sweep
PING_TARGETS = [
    ("R1", "10.0.24.1"),
    ("SW-1", "10.0.24.11"),
    ("lab-srv1", "10.0.24.10"),
    ("Wazuh Manager", "10.0.24.13"),
    ("GNS3 VM", "10.0.24.14"),
]

# Expected interfaces on R1 that should be up
R1_EXPECTED_UP = [
    "FastEthernet0/0", "FastEthernet0/0.9", "FastEthernet0/0.10",
    "FastEthernet0/0.11", "FastEthernet0/0.12", "FastEthernet0/0.13",
    "FastEthernet0/0.14", "FastEthernet0/0.15", "FastEthernet0/0.24",
    "Serial0/0",
]

# Legacy crypto for old Cisco IOS
LEGACY_DISABLED_ALGORITHMS = {
    'kex': [
        'diffie-hellman-group14-sha1',
        'diffie-hellman-group14-sha256',
        'ecdh-sha2-nistp256',
        'ecdh-sha2-nistp384',
        'ecdh-sha2-nistp521',
        'diffie-hellman-group-exchange-sha256',
        'diffie-hellman-group-exchange-sha1',
        'curve25519-sha256',
        'curve25519-sha256@libssh.org',
    ],
    'pubkeys': [
        'ssh-ed25519',
        'ecdsa-sha2-nistp256',
        'ecdsa-sha2-nistp384',
        'ecdsa-sha2-nistp521',
    ],
}


def connect_cisco(host, username, password):
    """Connect to a Cisco device via netmiko with legacy crypto support."""
    from netmiko import ConnectHandler
    dev = ConnectHandler(
        device_type='cisco_ios',
        host=host,
        username=username,
        password=password,
        secret=password,
        disabled_algorithms=LEGACY_DISABLED_ALGORITHMS,
        timeout=20,
    )
    return dev


def ping_sweep():
    """Ping all target devices and return reachability status."""
    results = []
    for name, ip in PING_TARGETS:
        try:
            result = subprocess.run(
                ["ping", "-c", "2", "-W", "2", ip],
                capture_output=True, text=True, timeout=10
            )
            reachable = result.returncode == 0
            # Extract RTT from last line
            rtt = "N/A"
            if reachable:
                lines = result.stdout.strip().split("\n")
                if lines:
                    m = re.search(r'= ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+)', lines[-1])
                    if m:
                        rtt = f"{m.group(1)}/{m.group(2)}/{m.group(3)} ms"
            results.append({
                "name": name,
                "ip": ip,
                "reachable": reachable,
                "rtt": rtt,
            })
        except Exception as e:
            results.append({
                "name": name,
                "ip": ip,
                "reachable": False,
                "rtt": "N/A",
                "error": str(e),
            })
    return results


def parse_interfaces(output):
    """Parse 'show ip interface brief' output into structured data."""
    interfaces = []
    for line in output.strip().split("\n"):
        if line.startswith("Interface") or not line.strip():
            continue
        parts = line.split()
        if len(parts) >= 6:
            interfaces.append({
                "interface": parts[0],
                "ip_address": parts[1] if parts[1] != "unassigned" else None,
                "method": parts[3] if len(parts) > 5 else "?",
                "status": parts[4] if len(parts) > 5 else parts[3],
                "protocol": parts[5] if len(parts) > 5 else parts[4],
            })
    return interfaces


def parse_cpu(output):
    """Parse 'show processes cpu' output for CPU utilization."""
    # First line: "CPU utilization for five seconds: 0%/0%; one minute: 1%; five minutes: 1%"
    m = re.search(
        r'five seconds: (\d+)%/(\d+)%; one minute: (\d+)%; five minutes: (\d+)%',
        output
    )
    if m:
        return {
            "five_sec": int(m.group(1)),
            "five_sec_interrupt": int(m.group(2)),
            "one_min": int(m.group(3)),
            "five_min": int(m.group(4)),
            "top_processes": [],
        }

    # Parse top processes
    procs = []
    for line in output.strip().split("\n"):
        m = re.match(
            r'\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+([\d.]+)%\s+([\d.]+)%\s+([\d.]+)%\s+(\d+)\s+(.+)',
            line
        )
        if m and float(m.group(5)) > 0:
            procs.append({
                "pid": int(m.group(1)),
                "process": m.group(9).strip(),
                "5sec": float(m.group(5)),
                "1min": float(m.group(6)),
                "5min": float(m.group(7)),
            })
    return {"top_processes": procs[:5]} if procs else {"top_processes": []}


def parse_route_summary(output):
    """Parse 'show ip route summary' for route count by protocol."""
    routes = {}
    for line in output.strip().split("\n"):
        m = re.match(r'^(\S+)\s+(\d+)\s+(\d+)\s+(\d+)', line)
        if m:
            routes[m.group(1)] = {
                "networks": int(m.group(2)),
                "subnets": int(m.group(3)),
                "overhead": int(m.group(4)),
            }
    return routes


def parse_interfaces_detail(output):
    """Parse 'show interfaces' for error counters on key interfaces."""
    interfaces = {}
    current_iface = None
    for line in output.split("\n"):
        # New interface header: "FastEthernet0/0 is up, line protocol is up"
        m = re.match(r'^(\S+(?:\.\d+)?)\s+is\s+(up|down|administratively down)', line)
        if m:
            current_iface = m.group(1)
            interfaces[current_iface] = {
                "status": m.group(2),
                "input_errors": 0,
                "output_errors": 0,
                "crc": 0,
                "runts": 0,
                "giants": 0,
                "input_drops": 0,
                "output_drops": 0,
                "reliability": "255/255",
                "txload": "0/255",
                "rxload": "0/255",
            }
        if current_iface:
            if "input errors" in line.lower():
                m = re.search(r'(\d+)\s+input errors', line, re.I)
                if m:
                    interfaces[current_iface]["input_errors"] = int(m.group(1))
                m = re.search(r'(\d+)\s+CRC', line, re.I)
                if m:
                    interfaces[current_iface]["crc"] = int(m.group(1))
                m = re.search(r'(\d+)\s+runts', line, re.I)
                if m:
                    interfaces[current_iface]["runts"] = int(m.group(1))
                m = re.search(r'(\d+)\s+giants', line, re.I)
                if m:
                    interfaces[current_iface]["giants"] = int(m.group(1))
                m = re.search(r'(\d+)\s+input drops', line, re.I)
                if m:
                    interfaces[current_iface]["input_drops"] = int(m.group(1))
            if "output errors" in line.lower():
                m = re.search(r'(\d+)\s+output errors', line, re.I)
                if m:
                    interfaces[current_iface]["output_errors"] = int(m.group(1))
                m = re.search(r'(\d+)\s+output drops', line, re.I)
                if m:
                    interfaces[current_iface]["output_drops"] = int(m.group(1))
            if "reliability" in line.lower():
                m = re.search(r'reliability\s+(\d+/\d+).*?txload\s+(\d+/\d+).*?rxload\s+(\d+/\d+)', line, re.I)
                if m:
                    interfaces[current_iface]["reliability"] = m.group(1)
                    interfaces[current_iface]["txload"] = m.group(2)
                    interfaces[current_iface]["rxload"] = m.group(3)
    return interfaces


def parse_ospf_neighbors(output):
    """Parse 'show ip ospf neighbor' output."""
    neighbors = []
    for line in output.strip().split("\n"):
        if line.startswith("Neighbor ID") or not line.strip():
            continue
        parts = line.split()
        if len(parts) >= 6:
            neighbors.append({
                "neighbor_id": parts[0],
                "priority": parts[1],
                "state": parts[2],
                "dead_time": parts[3],
                "address": parts[4],
                "interface": parts[5],
            })
    return neighbors


def parse_dhcp_pools(output):
    """Parse 'show ip dhcp pool' output for pool utilization."""
    pools = []
    current_pool = None
    for line in output.strip().split("\n"):
        m = re.match(r'^Pool\s+(\S+)\s*:', line, re.I)
        if m:
            if current_pool:
                pools.append(current_pool)
            current_pool = {"name": m.group(1), "utilization": "N/A", "leased": 0, "excluded": 0}
        if current_pool:
            m = re.search(r'Utilization:\s+(\d+)%', line, re.I)
            if m:
                current_pool["utilization"] = f"{m.group(1)}%"
    if current_pool:
        pools.append(current_pool)
    return pools


def collect_r1_data(dev):
    """Collect all R1 data in a single SSH session."""
    data = {}

    # Interface brief
    output = dev.send_command("show ip interface brief")
    data["interfaces"] = parse_interfaces(output)
    data["interfaces_raw"] = output

    # CPU
    output = dev.send_command("show processes cpu | ex 0.00")
    data["cpu"] = parse_cpu(output)
    data["cpu_raw"] = output

    # Route summary
    output = dev.send_command("show ip route summary")
    data["routes"] = parse_route_summary(output)
    data["routes_raw"] = output

    # Interface details (error counters) - focus on key sub-interfaces
    output = dev.send_command("show interfaces")
    data["interface_details"] = parse_interfaces_detail(output)

    # OSPF neighbors
    output = dev.send_command("show ip ospf neighbor")
    data["ospf_neighbors"] = parse_ospf_neighbors(output)
    data["ospf_raw"] = output

    # DHCP pools
    output = dev.send_command("show ip dhcp pool")
    data["dhcp_pools"] = parse_dhcp_pools(output)

    # Interface stats (for bandwidth/utilization)
    output = dev.send_command("show interfaces stats")
    data["interface_stats_raw"] = output[:2000]  # limit size

    return data


def collect_sw1_data(dev):
    """Collect SW-1 data."""
    data = {}

    output = dev.send_command("show ip interface brief")
    data["interfaces"] = parse_interfaces(output)
    data["interfaces_raw"] = output

    output = dev.send_command("show interfaces")
    data["interface_details"] = parse_interfaces_detail(output)

    output = dev.send_command("show processes cpu | ex 0.00")
    data["cpu"] = parse_cpu(output)
    data["cpu_raw"] = output

    return data


def main():
    """Main collection function — outputs JSON to stdout."""
    report = {
        "scan_time": datetime.now(timezone.utc).isoformat(),
        "lab": "Network Foundry",
    }

    # 1. Ping sweep
    report["reachability"] = ping_sweep()

    # 2. R1 data
    r1_data = {}
    try:
        dev = connect_cisco(R1_HOST, R1_USER, R1_PASS)
        r1_data = collect_r1_data(dev)
        r1_data["connected"] = True
        dev.disconnect()
    except Exception as e:
        r1_data = {"connected": False, "error": str(e)}
    report["r1"] = r1_data

    # 3. SW-1 data
    sw1_data = {}
    try:
        dev = connect_cisco(SW1_HOST, SW1_USER, SW1_PASS)
        sw1_data = collect_sw1_data(dev)
        sw1_data["connected"] = True
        dev.disconnect()
    except Exception as e:
        sw1_data = {"connected": False, "error": str(e)}
    report["sw1"] = sw1_data

    # 4. Summary for the agent
    unreachable = [d["name"] for d in report["reachability"] if not d["reachable"]]
    r1_down_interfaces = []
    if "interfaces" in r1_data:
        for iface in r1_data["interfaces"]:
            if iface["interface"] in R1_EXPECTED_UP and iface["status"] != "up":
                r1_down_interfaces.append(iface["interface"])

    r1_cpu = r1_data.get("cpu", {}).get("five_min", 0)
    r1_cpu_high = r1_cpu > 50

    r1_ospf_count = len(r1_data.get("ospf_neighbors", []))
    r1_ospf_expected = 1  # R2-ISP stub

    # Check for interface errors
    interface_errors = []
    for iface_name, details in r1_data.get("interface_details", {}).items():
        if details.get("input_errors", 0) > 0 or details.get("crc", 0) > 0 or details.get("output_errors", 0) > 0:
            interface_errors.append({
                "interface": iface_name,
                "input_errors": details.get("input_errors", 0),
                "crc": details.get("crc", 0),
                "output_errors": details.get("output_errors", 0),
                "reliability": details.get("reliability", "?"),
            })

    report["summary"] = {
        "unreachable_devices": unreachable,
        "r1_connected": r1_data.get("connected", False),
        "r1_down_interfaces": r1_down_interfaces,
        "r1_cpu_5min": r1_cpu,
        "r1_cpu_high": r1_cpu_high,
        "r1_ospf_neighbors": r1_ospf_count,
        "r1_ospf_expected": r1_ospf_expected,
        "r1_interface_errors": interface_errors,
        "sw1_connected": sw1_data.get("connected", False),
        "noteworthy": (
            len(unreachable) > 0
            or len(r1_down_interfaces) > 0
            or r1_cpu_high
            or r1_ospf_count != r1_ospf_expected
            or len(interface_errors) > 0
            or not r1_data.get("connected", False)
            or not sw1_data.get("connected", False)
        ),
    }

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()