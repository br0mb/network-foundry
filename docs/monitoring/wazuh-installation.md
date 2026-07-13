# Wazuh Agent Installation -- LAB-SRV1

> **Device:** lab-srv1 (Ubuntu 26.04 LTS)
> **Interface Monitored:** ens33 (10.0.24.10/21)
> **Wazuh Manager IP:** 10.0.24.14 (at installation time — later moved to 10.0.24.13, see troubleshooting docs)
> **Installation Date:** 2026-05-17
> **Installed By:** Admin

---

## Technical Overview

**Target Endpoint:** LAB-SRV1
**Operating System:** Ubuntu 26.04 LTS (Resolute Raccoon)
**Target Interface Monitored:** ens33 (10.0.24.10/21)
**Central SIEM Manager IP:** 10.0.24.14 (at installation time)

---

## Step 1: Secure Repository GPG Key Provisioning

To prevent file system permission loops common in older pipeline commands, a secure binary GPG keyring was generated under the root-protected keyrings folder.

```bash
curl -s https://packages.wazuh.com/key/GPG-KEY-WAZUH | gpg --dearmor | sudo tee /usr/share/keyrings/wazuh.gpg > /dev/null
```

**Verification:**
```bash
ls -l /usr/share/keyrings/wazuh.gpg
# Output: -rw-r--r-- 1 root root 2235 /usr/share/keyrings/wazuh.gpg
```

---

## Step 2: Custom Repository Mapping

The stable 4.x package stream was added directly to the local package management sources, strictly mapped to utilize the verified GPG keyring.

```bash
echo "deb [signed-by=/usr/share/keyrings/wazuh.gpg] https://packages.wazuh.com/4.x/apt/ stable main" | sudo tee /etc/apt/sources.list.d/wazuh.list
```

The database index was then forced to synchronize with the new remote endpoint:

```bash
sudo apt-get update
```

---

## Step 3: Inline Agent Deployment

The deployment utilized Wazuh's automated provisioning variables. By initializing the target manager IP inline with the compilation call, the system pre-configured `/var/ossec/etc/ossec.conf` automatically during installation.

```bash
sudo WAZUH_MANAGER="10.0.24.14" apt-get install wazuh-agent
```

---

## Step 4: Systemd Service Lifecycle Configuration

The system configuration manager was reloaded, the worker daemon was appended to the persistent boot profile, and the processing engine was initialized.

```bash
sudo systemctl daemon-reload
sudo systemctl enable wazuh-agent
sudo systemctl start wazuh-agent
```

---

## Step 5: Post-Deployment Verification

Running `sudo systemctl status wazuh-agent` confirmed successful validation and active socket runtime:

- **Service State:** active (running)

**Active Daemons Triggered:**
- `wazuh-agentd` -- Manager Communications
- `wazuh-execd` -- Active Response Framework
- `wazuh-syscheckd` -- File Integrity Monitoring & Rootkit Detection
- `wazuh-logcollector` -- Syslog & Auth Log Pipeline parsing
- `wazuh-modulesd` -- System Vulnerability Assessment & Policy Monitoring

---

## Step 6: Recommended Version Locking (Optional Maintenance Step)

To ensure system updates (`apt upgrade`) do not break compatibility by drifting ahead of your central manager version, lock the package version in place:

```bash
echo "wazuh-agent hold" | sudo dpkg --set-selections
```

---

## Verification Commands

```bash
# Check agent status
sudo systemctl status wazuh-agent

# Check agent logs
sudo tail -f /var/ossec/logs/ossec.log

# Check agent configuration
sudo cat /var/ossec/etc/ossec.conf | grep -A5 "<address>"

# Check running processes
ps aux | grep wazuh
```

---

## Post-Installation Verification (Completed 2026-05-17)

### Agent Registration Check (on Wazuh Manager)

```bash
sudo /var/ossec/bin/agent_control -l
```

**Result:**
```
Wazuh agent_control. List of available agents:
   ID: 000, Name: wazuh-server (server), IP: 127.0.0.1, Active/Local
   ID: 002, Name: CORE-SRV1, IP: any, Disconnected
   ID: 003, Name: lab-srv1, IP: any, Active
```

**Status:** ✅ lab-srv1 (ID 003) is **Active** and communicating with the Manager.

### Notes
- CORE-SRV1 (ID 002) is a disconnected legacy agent from the OIT capstone project. Kept as documentation/artifact.
- No agentless devices configured yet.

---

## Architecture

```
[lab-srv1] --Wazuh Agent--> [Wazuh Manager 10.0.24.14]
    ens33: 10.0.24.10/21          Dashboard: https://10.0.24.14:5601
```

> **Note:** The Wazuh Manager IP was later changed from .14 to .13 during VMware reconfiguration (2026-07-09). The current dashboard URL is `https://10.0.24.13` (port 443). See the troubleshooting docs for details.

---

## Dashboard Access

- **URL (at installation time):** `https://10.0.24.14:5601`
- **Current URL:** `https://10.0.24.13` (port 443, self-signed cert)
- **Default credentials:** `admin` / `[REDACTED]` or `wazuh-user` / `[REDACTED]`
- **Agent visible in dashboard:** lab-srv1 (ID 003)

---

## Related Files
- [[Wazuh Installation Log - OIT.CAPSTONE]] -- Original OIT capstone installation notes
- [[Wazuh Filter Tuning]] -- Filter configuration notes
- [[LAB-SRV1]] -- Server SOP
- [[Network Reference]] -- Full network documentation