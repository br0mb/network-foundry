# Network Foundry — AI-Augmented Network Operations Lab

> An enterprise network lab simulating a small business environment with 8+ VLANs, inter-VLAN routing, Active Directory, SIEM security monitoring, SNMP network monitoring, and AI-augmented operations agents.

## Overview

Network Foundry is a fully functional enterprise network lab built from scratch using physical Cisco hardware, virtual machines, Linux servers, and AI agent orchestration. It demonstrates network engineering, security operations, automation, and AI-augmented monitoring skills in a production-like environment.

## Key Features

### Network Infrastructure
- **Cisco 2650XM router** — inter-VLAN routing for 8+ VLANs, OSPF, DHCP server
- **Cisco 3750 core switch** — 802.1Q trunking, VLAN segmentation, spanning tree
- **/16 enterprise network** (10.0.0.0/16) divided into /21 blocks with further subnetting
- **Samba Active Directory** — domain controller with Kerberos, DNS, LDAP, and SMB
- **DNS architecture** — loop-free forwarding chain with internal/external resolution

### Security Monitoring (Wazuh SIEM)
- Wazuh Manager with OpenSearch indexer
- REST API integration for automated alert collection
- Rootkit detection (rootcheck), file integrity monitoring (syscheck)
- Vulnerability assessment
- Compliance mapping (PCI-DSS, HIPAA, NIST 800-53)
- Agent-based monitoring of domain controller

### Network Monitoring (Zabbix)
- SNMP polling of Cisco infrastructure (router + switch)
- Real-time dashboards for interface status, CPU, memory, bandwidth
- Interface error counter tracking (CRC, runts, giants, drops)
- OSPF adjacency monitoring
- DHCP pool utilization tracking
- 117 items monitored on router, 259 on switch

### AI-Augmented Operations
Three specialized agents inspired by Cisco's AgenticOps operating model:

1. **Security Monitor Agent** — queries Wazuh API and OpenSearch indexer every 30 minutes, filters false positives, generates Obsidian-formatted security reports with compliance mapping
2. **Network NOC Simulator Agent** — SSHes into Cisco devices hourly via Netmiko, collects interface/CPU/routing/OSPF data, generates NOC Tier 1/2 shift reports with P1-P5 incident classification and learning context
3. **Password Reset Agent** — restricted service account with three-layer security (SSH key-only access, sudoers lockdown to single wrapper script, dynamic admin blocklist with Domain Admins group verification)

### Production-Safe Architecture
- **Jump box deployment model** — dedicated VM on management VLAN with firewall-restricted outbound access
- **No software installed on production systems** — agents query existing APIs and SSH endpoints
- **Read-only access** — show commands only on Cisco devices, read-only API scope on SIEM
- **Full audit logging** — all actions logged to syslog, SSH sessions logged on target devices
- **Disposable infrastructure** — VM can be snapshotted, backed up, and rebuilt in minutes

## Repository Structure

```
network-foundry/
├── README.md                          # This file
├── LICENSE                            # MIT License
├── docs/
│   ├── network-design/                # Network topology and architecture
│   │   ├── network-reference.md      # Complete network documentation
│   │   └── subnet-allocation.md      # VLAN and subnet design
│   ├── device-configs/                # Cisco device configurations
│   │   ├── r1-core-router.md          # R1 running config
│   │   └── sw1-core-switch.md         # SW-1 running config
│   ├── monitoring/                    # Monitoring setup guides
│   │   ├── wazuh-installation.md      # Wazuh SIEM setup
│   │   ├── zabbix-installation.md     # Zabbix monitoring setup
│   │   └── snmp-configuration.md      # SNMP configuration guide
│   ├── troubleshooting/               # Troubleshooting case studies
│   │   ├── wazuh-dashboard-access.md  # Windows firewall + cert troubleshooting
│   │   ├── vm-ip-instability.md       # DHCP/static IP conflict resolution
│   │   └── dns-setup.md               # DNS record creation and resolution
│   └── ai-agents/                     # AI agent architecture and design
│       ├── agent-architecture.md      # Overview of the three-agent system
│       └── jump-box-architecture.md   # Production-safe deployment model
├── scripts/                           # Python collection scripts
│   ├── wazuh-collect.py               # Wazuh API + OpenSearch data collection
│   ├── network-collect.py             # Cisco SSH health check collection
│   └── pwdreset-wrapper.sh            # Restricted password reset wrapper
└── setup/
    ├── required-software.md           # Software requirements
    └── vm-setup-guide.md              # VM configuration guide
```

## Sanitization Notice

All credentials, passwords, API keys, personal names, and email addresses have been replaced with `[REDACTED]` placeholders or generic values. Private IP addresses (10.0.x.x) are retained as they are non-routable lab addresses. This repository is safe for public viewing.

**Note:** To reproduce this lab, replace all `[REDACTED]` placeholders with your own credentials and adjust IP addresses to match your network environment. The technical steps, architecture, and code structure are complete, only the secrets have been removed.

## Skills Demonstrated

| Category | Skills |
|----------|--------|
| Network Engineering | VLAN design, inter-VLAN routing, OSPF, subnetting, 802.1Q trunking, DNS architecture |
| Security Operations | Wazuh SIEM, OpenSearch, alert analysis, rootkit detection, FIM, compliance mapping |
| Network Monitoring | Zabbix, SNMP v2c, Cisco IOS SNMP templates, real-time dashboards |
| Automation | Python, Netmiko SSH, REST API integration, cron scheduling, automated reporting |
| Identity Management | Samba AD, Kerberos, LDAP, least-privilege design, sudoers lockdown, audit logging |
| AI Agent Development | Hermes Agent framework, governed execution, NOC workflow simulation, helpdesk automation |
| Documentation | Obsidian vault, wikilinks, troubleshooting logs, architectural diagrams |

## Related Concepts

- **Cisco AgenticOps** — This lab independently arrived at the same architectural principles Cisco describes in their AgenticOps operating model: governed execution, specialized agents, shared operational context, and human-in-the-loop control
- **Jump Box Architecture** — Production-safe deployment pattern using a dedicated, hardened VM with firewall-restricted outbound access to specific endpoints only

## License

MIT License — see LICENSE file for details

## Author

Network engineer and CCNP candidate with a BS in Cybersecurity (Summa Cum Laude). Built this lab to demonstrate enterprise network engineering, security operations, and AI-augmented monitoring skills.

## AI Assistance Disclosure

All network infrastructure, device configurations, security architecture, and troubleshooting were designed and implemented by the author. AI assistance was used to co-author documentation and generate collection scripts based on the author's specifications and architectural decisions. The AI agent orchestration layer (monitoring agents, password reset agent, jump box architecture) was designed by the author with AI-assisted implementation.