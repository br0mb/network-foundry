# Network Foundry -- Complete Reference

> **Last Updated:** 2026-07-10
> **Author:** Admin (with AI-Agent)
> **Purpose:** Complete documentation of the Network Foundry lab network, all aliases, port decisions, and Samba AD DC installation
> **Change Log (2026-07-09):** Updated Wazuh Manager IP (.14→.13), GNS3 VM IP (.13→.14), Wazuh dashboard URL (port 5601→443), removed Desktop NIC (.120, former VMware VMnet virtual IP no longer in use after bridged networking reconfiguration), updated Wazuh alias, added Wazuh API and indexer details, added Wazuh dashboard troubleshooting reference
> **Change Log (2026-07-10):** All VM IPs now static (Wazuh=.13 via systemd-networkd, GNS3=.14 via netplan, lab-srv1=.10 already static). Cloud-init disabled on both VMs. R1 DHCP exclusions added for .13-.15. Windows NIC reverted to .15. Wazuh alias updated in .bashrc. Zabbix PHP PCRE JIT warning fixed. SNMP not yet enabled on Cisco devices (pending).

---

## 1. Network Overview

Network Foundry is a hybrid physical/virtual enterprise lab built around a Cisco /16 network core, with an Ubuntu Server running Samba Active Directory Domain Controller. The environment supports network engineering practice, SOC tooling development, and AI-augmented operations.

### 1.1 Topology Summary

```
Internet (Xfinity)
    |
    | NAT/Firewall (Xfinity Router -- 192.168.68.1)
    |
    +--[WiFi]-- Laptop (WSL) -- eth2: 192.168.68.18/22
    |               |
    |               +-- eth1: 10.0.24.15/21 (lab network, mirrored mode)
    |               |    (Windows adapter "Server VLAN24" set to 10.0.24.15/21, Private network profile)
    |               |    (Note: WSL mirrored mode duplicates .15 — cosmetic "Duplicate" flag, does not affect functionality)
    |               |
    |               +-- VMnet (bridged Wi-Fi)
    |
    +--[Lab Switch]-- 10.0.24.0/21
                    |
                    +-- R1 (10.0.24.1) -- Core Cisco 2650XM router
                    |     |-- Fa0/0.9  (10.0.8.1)    -- Guest VLAN (/23)
                    |     |-- Fa0/0.10 (10.0.10.1)   -- IT Staff VLAN (/24)
                    |     |-- Fa0/0.11 (10.0.11.1)   -- Engineering VLAN (/24)
                    |     |-- Fa0/0.12 (10.0.12.1)   -- Finance VLAN (/24)
                    |     |-- Fa0/0.13 (10.0.13.1)   -- HR VLAN (/24)
                    |     |-- Fa0/0.14 (10.0.14.1)   -- Printers VLAN (/24)
                    |     |-- Fa0/0.15 (10.0.15.1)   -- Management VLAN (/24)
                    |     |-- Fa0/0.24 (10.0.24.1)   -- Infrastructure VLAN (/21)
                    |     |-- Ser0/0  (10.0.0.249)   -- R2-ISP (OSPF demo stub)
                    |
                    +-- lab-srv1 (10.0.24.10) -- Samba AD DC
                    |     |-- ens33: 10.0.24.10/21  (lab network)
                    |     |-- ens37: 192.168.68.14/22 (bridged Wi-Fi, internet)
                    |
                    +-- SW-1 (10.0.24.11) -- Core Switch
                    +-- Wazuh Manager (10.0.24.13) -- SIEM/XDR
                    |     |-- Dashboard: https://10.0.24.13 (port 443)
                    |     |-- API: https://10.0.24.13:55000
                    |     |-- Indexer (OpenSearch): localhost:9200 (not externally accessible)
                    |     |-- SSH: wazuh-user@10.0.24.13
                    |
                    +-- GNS3 VM (10.0.24.14) -- Network simulation
                    |     |-- Web UI: http://10.0.24.14 (port 80)
                    |     |-- SSH: gns3@10.0.24.14 (password: [REDACTED])
                    |     |-- Network Config: netplan (`/etc/netplan/01-netcfg.yaml`), cloud-init disabled, default GNS3 netplan configs renamed to .bak
                    |
                    +-- Desktop Host (VMware host, bridged networking)
                          |-- VMs bridge at Layer 2 through host NIC
                          |-- No host-side virtual IP on lab network (removed during bridged reconfiguration)
```

### 1.2 Active Subnet Allocation (/21 blocks)

| Block | Subnet | VLAN | Purpose | DHCP |
|-------|--------|------|---------|------|
| 10.0.0.0/21 | 10.0.0.0/24 | 5 | Physical interfaces | Static |
| 10.0.8.0/21 | 10.0.8.0/23 | 9 | Guests | R1 DHCP |
| | 10.0.10.0/24 | 10 | IT Staff | R1 DHCP |
| | 10.0.11.0/24 | 11 | Engineering | R1 DHCP |
| | 10.0.12.0/24 | 12 | Finance | R1 DHCP |
| | 10.0.13.0/24 | 13 | Human Resources | R1 DHCP |
| | 10.0.14.0/24 | 14 | Printers | R1 DHCP |
| | 10.0.15.0/24 | 15 | Management | R1 DHCP |
| 10.0.16.0/21 | 10.0.16.0/22 | 17 | DMZ | R1 DHCP |
| | 10.0.20.0/23 | 18 | Experimental | R1 DHCP |
| | 10.0.22.0/24 | 19 | IDS | R1 DHCP |
| | 10.0.23.0/25 | 20 | IPS | R1 DHCP |
| | 10.0.23.128/26 | 21 | Failover | R1 DHCP |
| | 10.0.23.192/26 | 22 | Firewall | R1 DHCP |
| 10.0.24.0/21 | 10.0.24.0/21 | 24 | Infrastructure | R1 DHCP |

---

## 2. Key Devices

### 2.1 R1 -- Core Router

- **Model:** Cisco 2650XM
- **IOS:** 12.4(15)T4
- **IP:** 10.0.24.1/21
- **Role:** Core routing, inter-VLAN routing, DHCP server
- **Default Gateway:** 10.0.24.2 (R2-ISP, OSPF demo stub)
- **SSH:** Legacy crypto required (diffie-hellman-group1-sha1)
- **No internet connectivity** (R2-ISP is a non-functional demo stub)
- **DNS:** Forwards to Samba DC (10.0.24.10)

### 2.2 lab-srv1 -- Samba AD DC

- **OS:** Ubuntu Server 26.07.04 LTS
- **Samba:** v4.23.6
- **Role:** Active Directory Domain Controller, DNS, DHCP (future)
- **Interfaces:**
  - `ens33` -- 10.0.24.10/21 (internal lab network)
  - `ens37` -- 10.0.0.135/24 (bridged Wi-Fi, internet-facing)
- **Domain:** lab.local (NetBIOS: LAB)
- **Firewall:** UFW -- ens37 allows only SSH (22); ens33 allows all

### 2.3 Laptop (WSL)

- **OS:** WSL2 Ubuntu on Windows 11 (hostname: Desktop-LR34T)
- **WSL IP:** 172.25.251.154/20 (Hyper-V virtual network)
- **Lab IP (WSL):** 10.0.24.15/21 (mirrored mode on eth1)
- **Lab IP (Windows):** 10.0.24.15/21 (adapter "Server VLAN24", static, Private network profile)
- **Internet:** 192.168.68.18/22 (Wi-Fi)
- **Network Profile:** Server VLAN24 adapter set to Private (required for browser access to lab web interfaces)
- **Note:** WSL mirrored mode duplicates the Windows IP — shows as "Duplicate" in ipconfig. This is cosmetic and does not affect functionality.
- **Aliases:** All network access aliases defined here

### 2.4 Wazuh Manager -- SIEM/XDR

- **IP:** 10.0.24.13 (static, configured via systemd-networkd)
- **OS:** Amazon Linux 2023
- **Wazuh Version:** v4.14.2
- **Network Config:** systemd-networkd (`/etc/systemd/network/10-cloud-init-eth0.network`), cloud-init disabled
- **Dashboard:** https://10.0.24.13 (port 443, self-signed cert)
- **REST API:** https://10.0.24.13:55000 (credentials: wazuh:[REDACTED], JWT auth)
- **Indexer (OpenSearch):** localhost:9200 only (not externally accessible; query via SSH)
- **SSH:** wazuh-user@10.0.24.13 (password: [REDACTED], requires `-o ConnectTimeout=15 -o PreferredAuthentications=password`)
- **Agents:**
  - ID 000: wazuh-server (active, local)
  - ID 002: CORE-SRV1 (disconnected, legacy Windows Server 2019)
  - ID 003: lab-srv1 (active, Ubuntu)
- **Note:** The Wazuh dashboard self-signed certificate may require accepting the cert warning in browser. See [[Wazuh-Dashboard-Access]] for troubleshooting.

### 2.5 R2-ISP (Demo Stub)

- **IP:** 10.0.24.2
- **Connected via:** R1 Serial0/0 (10.0.0.248/30)
- **Role:** Surface-level demo only -- advertises OSPF routes, no actual internet forwarding
- **Note:** Pings to 10.0.24.2 fail; this is expected behavior

---

## 3. WSL Network Aliases

All aliases are defined in `~/.bashrc` on the laptop (WSL).

| Alias | Command | Purpose |
|-------|---------|---------|
| `r1ssh` | Interactive SSH to R1 via netmiko | Access R1 CLI from terminal. Uses netmiko Python library with legacy crypto support. Interactive session with `exit` to quit. |
| `r1check` | `python3 .../health_check.py --save` | Runs automated health check on R1. Pulls version, interfaces, routes, VLANs, CDP neighbors. Saves results to `logs/`. |
| `r1backup` | `python3 .../backup_configs.py` | Backs up R1 running-config to timestamped file in `logs/`. |
| `srv1` | `ssh admin@10.0.24.10` | SSH into lab-srv1 as admin (key auth). |
| `srv1-agent` | `ssh ai-agent@10.0.24.10` | SSH into lab-srv1 as AI-Agent account (key auth, passwordless sudo). |
| `socmc` | `python3 .../socmc.py` | SOC Master Controller -- interactive menu to launch SOC tools (log hunter, VirusTotal, email analyzer, mole catcher, ticket generator). |
| `wazuh` | `sshpass -p "[REDACTED]" ssh -o StrictHostKeyChecking=no -o Ciphers=aes256-gcm@openssh.com,aes128-gcm@openssh.com -o ConnectTimeout=15 -o PreferredAuthentications=password wazuh-user@10.0.24.13` | SSH into Wazuh Manager VM. |

### Alias Connection Details

| Alias | Host | IP | Auth Method | Notes |
|-------|------|-----|-------------|-------|
| `r1ssh` | R1 | 10.0.24.1 | Legacy crypto (diffie-hellman-group1-sha1) + key | Netmiko-based interactive session |
| `srv1` | lab-srv1 | 10.0.24.10 | SSH key | admin account |
| `srv1-agent` | lab-srv1 | 10.0.24.10 | SSH key | AI-Agent account, nopasswd sudo |
| `wazuh` | Wazuh Manager | 10.0.24.13 | Password ([REDACTED]) + modern ciphers | wazuh-user account |
| `socmc` | Local | N/A | N/A | Python menu script |

---

## 4. Samba AD DC Installation & Configuration

### 4.1 WSL Mirrored Networking

Before the server could reach both the lab network and the internet, WSL needed mirrored networking enabled:

```powershell
# Windows PowerShell (admin)
wsl --shutdown
Set-Content -Path "$env:USERPROFILE\.wslconfig" -Value "[wsl2]`nnetworkingMode=mirrored" -Encoding UTF8
wsl
```

This created `eth1` (10.0.24.15/21) as a mirror of the physical ethernet adapter connected to the lab network.

### 4.2 Ubuntu Server Network Setup

The VM has two network adapters in VMware:
1. **VMnet0** (Custom) -- 10.0.24.10/21, connected to lab network via core switch
2. **Bridged (Wi-Fi)** -- 10.0.0.135/24, internet access through Xfinity

```bash
# Ubuntu server -- verify interfaces
ip addr show ens33  # 10.0.24.10/21
ip addr show ens37  # 10.0.0.135/24
```

### 4.3 Samba AD DC Installation

```bash
# 1. Install dependencies
sudo apt update
sudo apt install -y samba samba-dsdb-modules samba-vfs-modules winbind ldb-tools krb5-user dnsutils samba-ad-provision samba-ad-dc

# 2. Stop default Samba services
sudo systemctl stop smbd nmbd winbind
sudo systemctl disable smbd nmbd winbind

# 3. Remove default smb.conf (provision will create new one)
sudo rm /etc/samba/smb.conf

# 4. Provision AD DC
sudo samba-tool domain provision \
  --server-role=dc \
  --use-rfc2307 \
  --dns-backend=SAMBA_INTERNAL \
  --realm=LAB.LOCAL \
  --domain=LAB \
  --adminpass='[REDACTED]' \
  --option="dns forwarder = 8.8.8.8" \
  --option="interfaces = lo ens33" \
  --option="bind interfaces only = yes"

# 5. Create systemd service (not auto-created on Ubuntu 26.04)
sudo tee /etc/systemd/system/samba-ad-dc.service << 'EOF'
[Unit]
Description=Samba Active Directory Domain Controller
After=network.target remote-fs.target nss-lookup.target
[Service]
Type=forking
ExecStart=/usr/libexec/samba/samba-dcerpcd
PIDFile=/run/samba/samba.pid
Restart=on-failure
RestartSec=5
[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable samba-ad-dc
sudo systemctl start samba-ad-dc

# 6. Create domain accounts
sudo samba-tool user create user [REDACTED] --given-name=Lab --surname=User
sudo samba-tool user create admin [REDACTED] --given-name=Lab --surname=Admin
sudo samba-tool user create ai-agent [REDACTED] --given-name=AI --surname=Agent
sudo samba-tool group addmembers "Domain Admins" user admin ai-agent

# 7. Create AI-Agent account on Linux system
sudo useradd -m -s /bin/bash ai-agent
sudo usermod -aG sudo ai-agent
echo "ai-agent ALL=(ALL) NOPASSWD:ALL" | sudo tee /etc/sudoers.d/ai-agent
sudo chmod 440 /etc/sudoers.d/ai-agent

# 8. Set up SSH key auth (from laptop)
ssh-copy-id -i ~/.ssh/id_ed25519.pub ai-agent@10.0.24.10
```

### 4.4 DNS Forwarding Configuration

The DNS forwarding chain was carefully configured to avoid loops:

```
DHCP Client -> R1 (10.0.24.1) -> Samba DC (10.0.24.10)
                                  -> lab.local: resolved locally
                                  -> external: forwarded to 8.8.8.8 (via ens37)
```

**Key DNS decisions:**
- R1 uses `ip name-server 10.0.24.10` (Samba DC) as its sole DNS server
- Samba DC uses `dns forwarder = 8.8.8.8` for external resolution
- The Samba DC's forwarder was changed from 10.0.24.1 (R1) to 8.8.8.8 to prevent a DNS loop
- R1 no longer runs `ip dns server` (caused CPU hog -- DNS Server process hit %SYS-3-CPUHOG)
- R1 DHCP pools hand out 10.0.24.1 as DNS server to all VLAN clients

---

## 5. Firewall & Port Decisions

### 5.1 UFW Firewall (lab-srv1)

```
Default: deny incoming, allow outgoing

ens37 (internet-facing, 10.0.0.135):
  ALLOW  22/tcp   SSH (management only)
  DENY   everything else

ens33 (lab network, 10.0.24.10):
  ALLOW  all       (full access for lab/AD services)
```

### 5.2 Samba AD DC Listening Ports

After hardening, Samba DC listens on ens33 and lo only:

| Port | Service | Interface | Purpose |
|------|---------|-----------|---------|
| 22 | SSH | 0.0.0.0 | Management (all interfaces for flexibility) |
| 53 | DNS | ens33, lo | Internal DNS resolution |
| 88 | Kerberos | ens33, lo | AD authentication |
| 135 | RPC | ens33, lo | RPC endpoint mapper |
| 139 | SMB | ens33, lo | NetBIOS session service |
| 389 | LDAP | ens33, lo | Directory queries |
| 445 | SMB | ens33, lo | File sharing |
| 464 | kpasswd | ens33, lo | Kerberos password change |
| 636 | LDAPS | ens33, lo | Secure LDAP |
| 3268 | GC | ens33, lo | Global Catalog |
| 3269 | GC SSL | ens33, lo | Global Catalog SSL |

**Note:** Samba's `interfaces = lo ens33` and `bind interfaces only = yes` settings should restrict binding, but the services were still binding to 0.0.0.0 at time of documentation. The UFW firewall compensates by blocking traffic on ens37.

### 5.3 R1 SSH

- Port 22 with legacy crypto only (diffie-hellman-group1-sha1)
- Key-based auth (`~/.ssh/r1_key`) + password fallback ([REDACTED])

---

## 6. Security Considerations

### 6.1 Threat Model

- **Xfinity NAT** provides basic protection from internet
- **ens37 is exposed** to Xfinity LAN (neighbors, guests could reach it)
- **ens37 firewall** blocks everything except SSH
- **Lab network (ens33)** is isolated behind R1 and switches -- assumed trusted

### 6.2 Credentials

| Account | Password | Notes |
|---------|----------|-------|
| R1 admin | [REDACTED] | Console + SSH |
| lab-srv1 admin | [REDACTED] | SSH key + password sudo |
| lab-srv1 ai-agent | [REDACTED] | SSH key + nopasswd sudo |
| LAB\Administrator | [REDACTED] | Domain admin |
| LAB\user | [REDACTED] | Domain admin |
| LAB\admin | [REDACTED] | Domain admin |
| LAB\ai-agent | [REDACTED] | Domain admin |
| Wazuh Manager wazuh-user | [REDACTED] | Wazuh SIEM dashboard |
| Zabbix Admin | [REDACTED] | Network monitoring dashboard |

**These are lab credentials for use in an isolated environment.**

### 6.3 Pending Hardening

- [ ] Bind Samba services strictly to ens33 (not 0.0.0.0)
- [ ] Disable password auth on SSH (keys only)
- [ ] Set up fail2ban for SSH brute force protection
- [ ] Configure Samba share permissions and ACLs
- [ ] Set up audit logging on the DC
- [ ] Consider moving ens37 to a dedicated management VLAN

---

## 7. Files & Locations

| File | Path | Purpose |
|------|------|---------|
| Devices inventory | `config/devices.yaml` | YAML device inventory for scripts |
| Netmiko base | `utils/netmiko_base.py` | Shared Cisco/Linux connection class |
| SSH connect | `netops/ssh_connect.py` | Interactive SSH shell |
| Health check | `netops/health_check.py` | Automated R1 health check |
| Config backup | `netops/backup_configs.py` | R1 config backup |
| SOC Master Controller | `soc/master_controller/socmc.py` | SOC tool launcher menu |
| R1 SSH script | `~/bin/r1ssh` | Expect-based SSH to R1 with netmiko |
| WSL config | `.wslconfig` | Mirrored networking mode |
| Bash aliases | `~/.bashrc` | All aliases |
| This file | `docs/network-design/network-reference.md` | Network reference doc |
| Wazuh Agent Install | `docs/monitoring/wazuh-installation.md` | Wazuh agent installation guide |

---

## 8. Troubleshooting Notes

### R1 DNS Server CPU Hog
**Problem:** After enabling `ip dns server` on R1, the DNS Server process consumed 53-64% CPU (1min/5min averages).
**Cause:** DNS forwarding loop between R1 and Samba DC.
**Fix:** Removed `ip dns server` from R1 entirely. R1 now uses Samba DC as its sole DNS server.

### Samba AD DC Service Not Starting
**Problem:** `samba-ad-dc.service` failed with exit code 203 (EXEC) on Ubuntu 26.04.
**Cause:** Ubuntu 26.04 doesn't auto-create the systemd service. The `samba-ad-dc` meta-package was also not installed initially.
**Fix:** Installed `samba-ad-dc` package, created custom systemd service file pointing to `/usr/libexec/samba/samba-dcerpcd`.

### Samba DC DNS Loop
**Problem:** External DNS resolution failed with "Invalid input detected" on R1.
**Cause:** Samba DC's `dns forwarder` was set to R1 (10.0.24.1), creating a forwarding loop: R1 -> Samba DC -> R1.
**Fix:** Changed Samba DC's `dns forwarder` to 8.8.8.8 directly.

### WSL Not Seeing Lab Network
**Problem:** WSL only showed the Hyper-V virtual network (172.25.x.x), not the 10.0.24.0/21 lab network.
**Fix:** Enabled `networkingMode=mirrored` in `.wslconfig`. This creates a virtual NIC mirroring the physical ethernet adapter.

### Wazuh Dashboard Inaccessible from Browser (2026-07-09)
**Problem:** Wazuh dashboard unreachable from desktop PC browser ("This site can't be reached") despite all Wazuh services running and network connectivity confirmed.
**Root Cause:** Windows network adapter ("Server VLAN24") classified as Public network profile — Windows Firewall blocked outbound HTTPS to lab devices. Additionally, the Wazuh dashboard had moved from `10.0.24.14:5601` (documented) to `https://10.0.24.13` (port 443).
**Fix:**
1. Changed network profile: `Set-NetConnectionProfile -InterfaceAlias "Server VLAN24" -NetworkCategory Private`
2. Updated browser URL to `https://10.0.24.13` (no port number needed)
3. Accept self-signed certificate warning in browser
**Full troubleshooting log:** See [[Wazuh-Dashboard-Access]] in the Troubleshooting folder

### Wazuh Agent on lab-srv1 Disconnected (2026-07-09)
**Problem:** Wazuh agent on lab-srv1 (ID 003) showing as disconnected for 52+ days.
**Root Cause:** The Wazuh manager IP changed from `10.0.24.14` to `10.0.24.13` during VMware reconfiguration, but the agent config at `/var/ossec/etc/ossec.conf` still pointed to the old address `.14` (now GNS3).
**Fix:** Updated the agent config on lab-srv1:
```bash
ssh ai-agent@10.0.24.10
sudo sed -i 's/<address>10.0.24.14<\/address>/<address>10.0.24.13<\/address>/' /var/ossec/etc/ossec.conf
sudo systemctl restart wazuh-agent
```
**Verification:** Agent status changed from "disconnected" to "active" with current keepalive timestamp.

### VM IP Addresses Swapping on Every Boot (2026-07-10)
**Problem:** GNS3 VM and Wazuh Manager VM swapping IPs between .13 and .14 on every boot, breaking monitoring scripts and agent configs.
**Root Cause:** Both VMs were using DHCP from R1's VLAN 24 pool. Whichever VM booted first grabbed the next available IP. Additionally, cloud-init was regenerating network configs on every boot, overriding any manual static IP settings.
**Fix:** Set static IPs on both VMs and disabled cloud-init:
- GNS3 VM (Ubuntu/netplan): Static .14 via `/etc/netplan/01-netcfg.yaml`, cloud-init disabled, default GNS3 netplan configs renamed to .bak
- Wazuh VM (Amazon Linux 2023/systemd-networkd): Static .13 via `/etc/systemd/network/10-cloud-init-eth0.network`, cloud-init disabled
- R1: Added `ip dhcp excluded-address 10.0.24.13 10.0.24.15` to prevent DHCP from assigning reserved IPs
**Full troubleshooting logs:** See [[GNS3-VM-IP-Instability]] and [[Wazuh-VM-Static-IP]]

### Zabbix PHP PCRE JIT Warning (2026-07-10)
**Problem:** Zabbix web UI displaying "preg_match(): Allocation of JIT memory failed, PCRE JIT will be disabled" warning.
**Root Cause:** PHP 8.5's PCRE JIT compilation could not allocate executable memory due to system security restrictions.
**Fix:** Added `pcre.jit=0` to `/etc/php/8.5/apache2/php.ini` and restarted Apache.
**Note:** This is a performance warning, not a functional error. Zabbix works correctly with JIT disabled — regex processing is slightly slower but functionally identical.