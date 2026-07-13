# Network Foundry AI Monitoring Jump Box — Concept & Architecture

> **Created:** 2026-07-09
> **Author:** Admin with AI-Agent
> **Purpose:** Production-safe deployment architecture for AI-augmented network monitoring
> **Status:** Conceptual design — ready for implementation

---

## 1. The Problem

The current Network Foundry monitoring setup runs the AI-Agent on the laptop with full network access. That's fine for a lab, but it's not deployable in a real enterprise NOC because:

- **Production systems are locked down.** Nobody lets you install AI software on a SIEM server, a domain controller, or a core router. These are change-controlled, audited, and often subject to compliance frameworks (PCI-DSS, SOC 2, FedRAMP).
- **The agent has too much access.** Running on the laptop with no firewall restrictions, the agent can reach every device on the lab network. If the agent is compromised or makes an error, the blast radius is the entire network.
- **It's not reproducible.** A monitoring system that depends on someone's personal laptop being on and connected is not an operations system — it's a science project.

---

## 2. The Solution: Monitoring Jump Box

The answer is the same pattern enterprises already use for secure administrative access: a **jump box** (also called a bastion host). A dedicated, hardened VM that serves as the single point of entry for monitoring queries.

### Key Principle

**The AI agent touches nothing on the production network. It queries existing APIs and SSH endpoints — exactly what a human NOC engineer would do from a jump box. The only difference is it does it automatically, on a schedule, and produces structured reports.**

---

## 3. Architecture

```
┌─────────────────────────────────────────────────────┐
│                  VMware Host (Desktop PC)            │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │         Monitoring Jump Box VM               │   │
│  │         (Ubuntu Server, minimal)             │   │
│  │                                              │   │
│  │  ┌────────────┐  ┌─────────────────────┐    │   │
│  │  │ AI-Agent   │  │ Collection Scripts  │    │   │
│  │  │ + Cron Jobs │  │ (Python + Netmiko)  │    │   │
│  │  └────────────┘  └─────────────────────┘    │   │
│  │                                              │   │
│  │  ┌──────────────────────────────────────┐   │   │
│  │  │  UFW Firewall — Outbound Rules Only  │   │   │
│  │  │                                      │   │   │
│  │  │  ALLOW → 10.0.24.13:55000 (Wazuh API)│   │   │
│  │  │  ALLOW → 10.0.24.13:443  (Wazuh dash)│   │   │
│  │  │  ALLOW → 10.0.24.1:22    (R1 SSH)    │   │   │
│  │  │  ALLOW → 10.0.24.11:22   (SW-1 SSH)  │   │   │
│  │  │  ALLOW → 10.0.24.10:22   (srv1 SSH)  │   │   │
│  │  │  DENY  → everything else             │   │   │
│  │  └──────────────────────────────────────┘   │   │
│  │                                              │   │
│  │  NIC: VMnet (bridged) → Management VLAN 15   │   │
│  │  IP: 10.0.15.50/24 (static)                  │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │  Other VMs (untouched)                       │   │
│  │  - lab-srv1 (10.0.24.10) — Samba AD DC      │   │
│  │  - Wazuh Manager (10.0.24.13) — SIEM         │   │
│  │  - GNS3 VM (10.0.24.14) — Network simulation│   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
                    │
                    │ Trunk port (802.1Q)
                    │
              ┌─────┴─────┐
              │  SW-1     │  Cisco 3750 Core Switch
              │ 10.0.24.11│
              └─────┬─────┘
                    │
              ┌─────┴─────┐
              │  R1       │  Cisco 2650XM Router
              │ 10.0.24.1 │  Inter-VLAN routing, OSPF, DHCP
              └───────────┘
```

---

## 4. Why This Is Production-Safe

| Concern | How the Jump Box Addresses It |
|---------|-------------------------------|
| No software installed on production systems | The jump box queries existing APIs (Wazuh REST API) and SSH endpoints (Cisco devices). Nothing is installed on the SIEM, routers, or domain controllers. |
| Limited blast radius | UFW firewall restricts outbound traffic to specific IPs and ports. If the VM is compromised, the attacker can only reach 5 endpoints on specific ports — not the entire network. |
| Read-only access | The monitoring scripts use `show` commands on Cisco devices (no config writes). The Wazuh API token has read-only access to alerts and agent status. The password reset agent uses a restricted sudo wrapper. |
| Auditable | All SSH sessions are logged on the target devices. The wrapper script logs to syslog. Cron job output is saved locally. Every action has an audit trail. |
| Disposable | The VM can be snapshotted, backed up, and rebuilt from scratch in minutes. No state lives on production systems — all config, scripts, and reports are on the VM. |
| Isolated | The VM sits on the management VLAN (VLAN 15), not the infrastructure VLAN. It has no access to user VLANs, the DMZ, or the internet. |

---

## 5. Network Placement

The jump box should sit on a **dedicated monitoring or management VLAN** — not the same VLAN as the infrastructure it's monitoring. In Network Foundry, VLAN 15 (Management, 10.0.15.0/24) is the natural fit.

```
VLAN 15 (Management) — 10.0.15.0/24
  Gateway: 10.0.15.1 (R1 Fa0/0.15)
  Jump Box: 10.0.15.50 (static)
```

This gives the jump box a route to all infrastructure devices via R1, but isolates it from user traffic on VLANs 10-14 and the DMZ on VLAN 17. If the jump box were on VLAN 24 (Infrastructure) alongside the servers, a compromise would put it on the same broadcast domain as its targets — harder to contain.

---

## 6. Firewall Rules (UFW)

```bash
# Default policies — deny all outbound, allow established inbound
sudo ufw default deny incoming
sudo ufw default deny outgoing
sudo ufw allow outgoing

# Allow SSH to the jump box itself (from management network only)
sudo ufw allow in on ens33 from 10.0.15.0/24 to any port 22 proto tcp

# Allow outbound to Wazuh API
sudo ufw allow out to 10.0.24.13 port 55000 proto tcp
# Allow outbound to Wazuh dashboard (for verification)
sudo ufw allow out to 10.0.24.13 port 443 proto tcp

# Allow outbound to R1 SSH
sudo ufw allow out to 10.0.24.1 port 22 proto tcp

# Allow outbound to SW-1 SSH
sudo ufw allow out to 10.0.24.11 port 22 proto tcp

# Allow outbound to lab-srv1 SSH (for password reset agent)
sudo ufw allow out to 10.0.24.10 port 22 proto tcp

# Allow outbound DNS (to Samba DC for name resolution)
sudo ufw allow out to 10.0.24.10 port 53 proto udp

# Enable firewall
sudo ufw enable
```

**Result:** The jump box can only talk to 5 specific endpoints on specific ports. Everything else is blocked — no lateral movement, no internet, no access to user VLANs.

---

## 7. What Runs on the Jump Box

| Component | Purpose | Installation |
|-----------|---------|---------------|
| AI-Agent | Cron scheduler + AI analysis | `curl install.sh \| bash` |
| Python 3 + venv | Collection scripts | Pre-installed on Ubuntu Server |
| Netmiko | Cisco SSH library | `pip install netmiko` (in venv) |
| sshpass | Wazuh SSH access | `apt install sshpass` |
| UFW | Firewall | Pre-installed on Ubuntu |
| SSH keys | Key-based auth to devices | Generated on VM, copied to targets |

**What does NOT run on the jump box:**
- No Wazuh agent (the jump box is not monitored by the SIEM — it IS the monitoring system)
- No Samba AD (no domain join — uses local accounts)
- No Docker, no containers, no unnecessary services
- No GUI/Desktop environment — headless server only

---

## 8. Credential Management

All credentials live on the jump box in a protected `.env` file (not readable by the agent):

```ini
# Wazuh API
WAZUH_API_USER=wazuh
WAZUH_API_PASS=[REDACTED]

# Indexer
INDEXER_USER=admin
INDEXER_PASS=[REDACTED]

# Cisco SSH (R1, SW-1)
CISCO_USER=admin
CISCO_PASS=[REDACTED]

# Password reset SSH key path
PWDRESET_KEY=~/.ssh/pwdreset_key
```

In a production environment, these would be stored in a secrets manager (HashiCorp Vault, AWS Secrets Manager) and rotated regularly. For the lab, `.env` is sufficient.

---

## 9. What Would Change in a Production NOC

| Lab Version | Production Version |
|-------------|-------------------|
| AI-Agent on laptop | AI-Agent on dedicated jump box VM |
| .env with plaintext creds | Secrets manager (Vault, AWS SM) |
| Reports to local Obsidian vault | Reports to ticketing system (ServiceNow, Jira) or SIEM directly |
| UFW on the VM | Network ACLs on the switch/firewall (Layer 3/4 enforcement) |
| Local cron scheduling | Enterprise scheduler (Ansible Tower, Rundeck) or container orchestration |
| No alerting to humans | Email/Slack/Teams alerts on P1/P2 incidents |
| Single jump box | Redundant jump boxes with load balancing |

The architecture scales. The jump box pattern works for a lab with 5 devices or an enterprise with 500 — you just add more endpoints to the firewall allowlist and scale the cron schedule.

---

## Related Files

- [[Network Reference]] — Full network documentation
- [[Network Foundry Portfolio]] — Lab portfolio
- [[Jump Box Implementation Guide]] — Step-by-step build guide