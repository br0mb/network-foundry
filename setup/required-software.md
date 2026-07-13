# Required Software — Network Foundry Lab

> **Purpose:** Complete list of software required to build and run the Network Foundry lab environment
> **Last Updated:** 2026-07-11

---

## Host Machine (Windows 11)

| Software | Purpose | Download |
|----------|---------|----------|
| **Windows Subsystem for Linux (WSL2)** | Linux environment for AI agents and automation | `wsl --install` in PowerShell |
| **VMware Workstation Pro** | Virtual machines for servers and network simulation | [vmware.com](https://www.vmware.com) |
| **Cisco Packet Tracer** | Network simulation and practice | [netacad.com](https://www.netacad.com) |
| **GNS3** | Advanced network simulation | [gns3.com](https://www.gns3.com) |
| **Obsidian** | Documentation and knowledge base | [obsidian.md](https://obsidian.md) |
| **PuTTY** | SSH client for network devices | [putty.org](https://www.putty.org) |
| **Visual Studio Code** | Code editing and development | [code.visualstudio.com](https://code.visualstudio.com) |

---

## WSL2 Environment

| Software | Purpose | Install Command |
|----------|---------|-----------------|
| **AI-Agent** | AI agent for network operations | Via API provider |
| **Python 3.x** | Automation scripting | `sudo apt install python3 python3-pip` |
| **Netmiko** | SSH to network devices (Cisco) | `pip3 install netmiko` |
| **Git** | Version control | `sudo apt install git` |
| **curl** | HTTP requests | `sudo apt install curl` |
| **sshpass** | Non-interactive SSH (for Wazuh) | `sudo apt install sshpass` |

---

## VMware Virtual Machines

| VM | OS | Purpose | IP |
|----|-----|---------|-----|
| **lab-srv1** | Ubuntu Server 26.04 LTS | Samba AD DC, DNS, Zabbix monitoring | 10.0.24.10/21 |
| **Wazuh Manager** | Amazon Linux 2023 | SIEM and security monitoring | 10.0.24.13/21 |
| **GNS3 VM** | GNS3 Appliance (Ubuntu) | Network simulation | 10.0.24.14/21 |

---

## Network Equipment (Physical)

| Device | Model | Role | IP |
|--------|-------|------|-----|
| **R1** | Cisco 2650XM | Core router, inter-VLAN routing, DHCP, OSPF | 10.0.24.1/21 |
| **SW-1** | Cisco WS-C3750 | Core switch, VLAN trunking | 10.0.24.11/21 |
| **SW-2** | Cisco WS-C3750 | Access switch | 10.0.24.12/21 |
| **R2-ISP** | Cisco 2650XM | OSPF demo stub | 10.0.24.2/21 |

---

## Monitoring Tools

| Tool | Purpose | Access URL |
|------|---------|------------|
| **Wazuh** | SIEM, security monitoring, log analysis, FIM, vulnerability detection | https://10.0.24.13 |
| **Zabbix** | Network monitoring, alerting, dashboards, SNMP polling | http://10.0.24.10/zabbix |

---

## AI Agents

| Agent | Platform | Purpose | Configuration |
|-------|----------|---------|---------------|
| **AI-Agent** | Cloud LLM API | Network automation, troubleshooting, documentation, security monitoring | API key in config file |

---

## Installation Order

1. **Windows host:** Install VMware Workstation, WSL2, Obsidian, VS Code, PuTTY
2. **WSL2:** Install Python 3, pip, Git, curl, Netmiko, sshpass
3. **VMware VMs:** Create and install Ubuntu Server (lab-srv1), Amazon Linux (Wazuh), GNS3 appliance
4. **Network equipment:** Configure R1, SW-1, SW-2 with VLANs, trunking, DHCP, OSPF
5. **Samba AD DC:** Provision domain on lab-srv1
6. **Wazuh:** Install Wazuh manager, indexer, dashboard
7. **Zabbix:** Install Zabbix server, agent, and configure SNMP monitoring
8. **SNMP:** Enable SNMP on Cisco devices for Zabbix polling
9. **AI-Agent:** Configure cron jobs for automated monitoring

---

## Related Files

- [[Network Reference]] — Full network documentation
- [[Wazuh Installation]] — Wazuh setup guide
- [[Zabbix Installation]] — Zabbix setup guide
- [[SNMP Configuration]] — SNMP setup guide