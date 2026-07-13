# Network Foundry Monitoring Jump Box — Implementation Guide

> **Created:** 2026-07-09
> **Author:** Admin with AI-Agent
> **Purpose:** Step-by-step guide to build the monitoring jump box VM
> **Prerequisites:** VMware Workstation/Player, Network Foundry lab online (R1, SW-1, lab-srv1, Wazuh)

---

## Overview

This guide walks through building a minimal Ubuntu Server VM that runs the Network Foundry monitoring agents in isolation. The VM has no software installed on production systems — it queries existing APIs and SSH endpoints via firewall-restricted outbound traffic.

**Time estimate:** 45-60 minutes
**VM specs:** 2 vCPU, 2GB RAM, 10GB disk, Ubuntu Server 24.04/26.04 LTS

---

## Phase 1: Create the VM

### Step 1: Create VM in VMware

1. Open VMware Workstation → Create a New Virtual Machine
2. Select Ubuntu Server ISO (24.04 LTS or 26.04 LTS)
3. **VM Settings:**
   - Name: `lab-monitor`
   - CPU: 2 vCPU
   - RAM: 2GB
   - Disk: 10GB (thin provisioned)
   - Network Adapter: **Bridged** (to lab network via host NIC)

4. **Do NOT add a second NIC.** Single adapter only — this VM should not have internet access.

### Step 2: Install Ubuntu Server

1. Boot from ISO, follow installer
2. **Network configuration:**
   - Set static IP: `10.0.15.50`
   - Subnet: `255.255.255.0` (/24)
   - Gateway: `10.0.15.1` (R1 Fa0/0.15)
   - DNS: `10.0.24.10` (Samba DC on lab-srv1)

3. **User setup:**
   - Username: `monitor`
   - Password: `[REDACTED]`
   - Hostname: `lab-monitor`
   - Install OpenSSH Server (select during installer)

4. After installation, remove the ISO and reboot

### Step 3: Verify Network Connectivity

```bash
# From the jump box VM:
ping 10.0.15.1     # R1 management interface — should respond
ping 10.0.24.1     # R1 infrastructure interface — should respond (routed)
ping 10.0.24.10    # lab-srv1 — should respond
ping 10.0.24.13    # Wazuh Manager — should respond
ping 10.0.24.11    # SW-1 — should respond
```

If any ping fails, verify:
- R1 has the VLAN 15 sub-interface configured (Fa0/0.15, 10.0.15.1/24)
- SW-1 has VLAN 15 in its VLAN database and the trunk port allows VLAN 15
- The VMware bridge is connected to the correct physical NIC

---

## Phase 2: Harden the VM

### Step 4: Update and Install Base Packages

```bash
# The VM has no internet access, so we can't apt update.
# Install packages from the ISO or skip updates.
# For the lab, the base install is sufficient.

# Verify required tools are present:
which python3       # should be pre-installed
which ssh           # should be pre-installed (openssh-server)
which ufw           # should be pre-installed
```

> **Note:** If the VM needs internet temporarily for package installation, add a second NIC (NAT or bridged to Wi-Fi) just for the install phase, then remove it. Never leave the monitoring VM with internet access in production.

### Step 5: Configure UFW Firewall

```bash
# Reset UFW to defaults
sudo ufw --force reset

# Default policies
sudo ufw default deny incoming
sudo ufw default deny outgoing

# Allow SSH to the jump box (from management network only)
sudo ufw allow in on ens33 from 10.0.15.0/24 to any port 22 proto tcp

# Allow outbound to Wazuh API (port 55000)
sudo ufw allow out to 10.0.24.13 port 55000 proto tcp

# Allow outbound to Wazuh dashboard (port 443 — for verification only)
sudo ufw allow out to 10.0.24.13 port 443 proto tcp

# Allow outbound to R1 SSH (port 22)
sudo ufw allow out to 10.0.24.1 port 22 proto tcp

# Allow outbound to SW-1 SSH (port 22)
sudo ufw allow out to 10.0.24.11 port 22 proto tcp

# Allow outbound to lab-srv1 SSH (port 22 — for password reset agent)
sudo ufw allow out to 10.0.24.10 port 22 proto tcp

# Allow outbound DNS to Samba DC (port 53 UDP)
sudo ufw allow out to 10.0.24.10 port 53 proto udp

# Enable firewall
sudo ufw --force enable

# Verify rules
sudo ufw status verbose
```

### Step 6: Verify Firewall Isolation

```bash
# Should succeed — allowed by firewall
curl -sk --connect-timeout 5 https://10.0.24.13:55000/security/user/authenticate -H "Authorization: Basic *** -n wazuh:[REDACTED] | base64)"

# Should fail — blocked by firewall (no rule for port 80 to Wazuh)
curl -sk --connect-timeout 5 http://10.0.24.14 2>&1 | head -2

# Should fail — blocked by firewall (GNS3 not in allowlist)
ping -c 2 10.0.24.14 2>&1
```

---

## Phase 3: Install Monitoring Stack

### Step 7: Install AI-Agent

```bash
# If the VM has no internet, you can:
# Option A: Temporarily add a NAT NIC for the install, then remove it
# Option B: Download the install script on another machine and transfer via SCP

# From a machine with internet, download the install script:
# scp <your-laptop>:~/ai-agent-install.sh monitor@10.0.15.50:~/

# Or if temporary internet is available:
curl -fsSL https://raw.githubusercontent.com/NousResearch/ai-agent/main/scripts/install.sh | bash

# Configure AI-Agent with the same model as the laptop:
ai-agent setup
# Select: ollama-cloud provider, GLM-5.2 model
# Enter OLLAMA_API_KEY when prompted
```

### Step 8: Install Python Dependencies

```bash
# Create a venv for the network monitoring scripts (needs netmiko)
python3 -m venv ~/.ai-agent/scripts/network-monitor-venv
source ~/.ai-agent/scripts/network-monitor-venv/bin/activate
pip install netmiko
deactivate

# Install sshpass (for Wazuh SSH access)
sudo apt install sshpass
```

### Step 9: Copy Collection Scripts

From your laptop, SCP the scripts to the jump box:

```bash
# From the laptop (or wherever the scripts currently live):
scp -r ~/.ai-agent/scripts/wazuh-monitor monitor@10.0.15.50:~/.ai-agent/scripts/
scp -r ~/.ai-agent/scripts/network-monitor monitor@10.0.15.50:~/.ai-agent/scripts/
scp -r ~/.ai-agent/scripts/network-monitor-venv monitor@10.0.15.50:~/.ai-agent/scripts/

# Copy the password reset skill
scp -r ~/.ai-agent/skills/devops/lab-password-reset monitor@10.0.15.50:~/.ai-agent/skills/devops/
```

### Step 10: Configure SSH Keys

The jump box needs SSH keys for the devices it monitors:

```bash
# On the jump box VM:
# Generate SSH keys for monitoring
ssh-keygen -t ed25519 -f ~/.ssh/monitor_key -N "" -C "lab-monitor@jumpbox"

# Copy key to R1 (uses legacy crypto — may need manual copy)
# R1 uses password auth, so copy manually:
ssh-copy-id -i ~/.ssh/monitor_key.pub admin@10.0.24.1

# Copy key to SW-1
ssh-copy-id -i ~/.ssh/monitor_key.pub admin@10.0.24.11

# For lab-srv1, copy the pwdreset key:
# Generate a new pwdreset key on the jump box
ssh-keygen -t ed25519 -f ~/.ssh/pwdreset_key -N "" -C "pwdreset-agent@jumpbox"

# Copy to lab-srv1 (need to do this as ai-agent user with sudo)
# First copy to ai-agent account:
scp ~/.ssh/pwdreset_key.pub ai-agent@10.0.24.10:/tmp/
# Then SSH in as ai-agent and install it for pwdreset user:
ssh ai-agent@10.0.24.10 'sudo mkdir -p /home/pwdreset/.ssh && sudo cp /tmp/pwdreset_key.pub /home/pwdreset/.ssh/authorized_keys && sudo chown -R pwdreset:pwdreset /home/pwdreset/.ssh && sudo chmod 700 /home/pwdreset/.ssh && sudo chmod 600 /home/pwdreset/.ssh/authorized_keys'
```

### Step 11: Configure AI-Agent Cron Jobs

On the jump box, configure the same two cron jobs:

```bash
# Wazuh SIEM Monitor — every 30 minutes
# Use AI-Agent CLI:
ai-agent cron create "*/30 * * * *" --name "Wazuh SIEM Security Monitor" \
  --script "wazuh-monitor/wazuh-collect.py" \
  --prompt "You are the Network Foundry Security Monitor Agent..." \
  --toolsets "file,terminal"

# Network NOC Monitor — every hour
ai-agent cron create "0 * * * *" --name "Network Foundry Network Monitor (NOC Simulator)" \
  --script "network-monitor/run-collect.sh" \
  --prompt "You are the Network Foundry Network Monitor Agent..." \
  --toolsets "file,terminal"
```

> **Note:** The full prompts are in the existing cron jobs on your laptop. You can export them with `ai-agent cron edit <job_id>` and copy the prompt text.

### Step 12: Configure Report Output Location

The jump box needs to write reports to a location you can access. Two options:

**Option A — Write to the jump box and SCP periodically:**
```bash
# Reports stay on the jump box at:
# ~/.ai-agent/reports/wazuh-siem/
# ~/.ai-agent/reports/network-monitor/
# 
# Pull them to your laptop when you want to review:
scp -r monitor@10.0.15.50:~/.ai-agent/reports/ ./jumpbox-reports/
```

**Option B — Mount a shared folder (if VMware shared folders are available):**
```bash
# In VMware: VM Settings → Options → Shared Folders → Enable
# Map to your Obsidian vault's AI-Agent folder
# The reports write directly to the vault.
```

**Option C — Send reports via email or webhook (production approach):**
```bash
# Configure a cron job post-processor that emails the report
# or sends it to a Slack/Teams webhook
# This is the production pattern — no manual pulling needed.
```

---

## Phase 4: Configure the Password Reset Agent

### Step 13: Create the lab-pwreset Profile on the Jump Box

```bash
# Create the profile
ai-agent profile create lab-pwreset

# Copy the SOUL.md from your laptop (or recreate it):
# scp ~/.ai-agent/profiles/lab-pwreset/SOUL.md monitor@10.0.15.50:~/.ai-agent/profiles/lab-pwreset/

# Copy the config.yaml (for model config):
cp ~/.ai-agent/config.yaml ~/.ai-agent/profiles/lab-pwreset/config.yaml

# Add the OLLAMA_API_KEY to the profile's .env:
echo "OLLAMA_API_KEY=[REDACTED]" >> ~/.ai-agent/profiles/lab-pwreset/.env

# Create the alias:
ai-agent profile alias lab-pwreset --name gopwreset
```

### Step 14: Create a Wrapper Script for Password Resets

The password reset wrapper script and the `pwdreset` user on lab-srv1 are already configured from the laptop setup. The jump box just needs SSH access as the `pwdreset` user, which was set up in Step 10.

Verify it works:

```bash
# From the jump box:
ssh -i ~/.ssh/pwdreset_key -o ConnectTimeout=10 -o StrictHostKeyChecking=no \
  -o UserKnownHostsFile=/dev/null pwdreset@10.0.24.10 \
  "sudo /usr/local/bin/pwdreset-wrapper.sh s.chen '[REDACTED]'"
# Should succeed

ssh -i ~/.ssh/pwdreset_key -o ConnectTimeout=10 -o StrictHostKeyChecking=no \
  -o UserKnownHostsFile=/dev/null pwdreset@10.0.24.10 \
  "sudo /usr/local/bin/pwdreset-wrapper.sh user 'Hacked!'"
# Should fail — admin blocked
```

---

## Phase 5: Verification & Testing

### Step 15: End-to-End Verification Checklist

```bash
# 1. Firewall is active and correct
sudo ufw status verbose
# → Should show deny incoming, specific outbound rules only

# 2. AI-Agent is running
ai-agent doctor
# → Should show all checks passing

# 3. Cron jobs are scheduled
ai-agent cron list
# → Should show two recurring jobs with next_run timestamps

# 4. Wazuh API is reachable
curl -sk https://10.0.24.13:55000/security/user/authenticate \
  -H "Authorization: Basic *** -n wazuh:[REDACTED] | base64)"
# → Should return a JWT token

# 5. R1 SSH works (via netmiko)
~/.ai-agent/scripts/network-monitor-venv/bin/python3 -c "
from netmiko import ConnectHandler
dev = ConnectHandler(device_type='cisco_ios', host='10.0.24.1',
    username='admin', password=os.getenv('CISCO_PASS'),
    disabled_algorithms={'kex':['diffie-hellman-group14-sha1',
    'diffie-hellman-group14-sha256','ecdh-sha2-nistp256',
    'ecdh-sha2-nistp384','ecdh-sha2-nistp521',
    'diffie-hellman-group-exchange-sha256',
    'diffie-hellman-group-exchange-sha1','curve25519-sha256',
    'curve25519-sha256@libssh.org'],
    'pubkeys':['ssh-ed25519','ecdsa-sha2-nistp256',
    'ecdsa-sha2-nistp384','ecdsa-sha2-nistp521']},
    timeout=15)
print(dev.send_command('show ip interface brief'))
dev.disconnect()
"
# → Should show R1 interface table

# 6. Password reset agent works
gopwreset chat -q "reset password for j.martinez"
# → Should confirm and reset

# 7. Admin reset is blocked
gopwreset chat -q "reset password for user"
# → Should refuse

# 8. GNS3 is NOT reachable (firewall working)
ping -c 2 10.0.24.14
# → Should fail — not in firewall allowlist

# 9. Internet is NOT reachable
ping -c 2 8.8.8.8
# → Should fail — no outbound internet rule
```

### Step 16: Snapshot the VM

```bash
# In VMware: VM → Snapshot → Take Snapshot
# Name: "Monitoring Jump Box — Baseline"
# Description: "Clean install with AI-Agent, scripts, firewall, and cron jobs configured"
```

This snapshot lets you roll back to a known-good state if anything breaks. In a production environment, this is your disaster recovery point.

---

## Phase 6: Production Considerations

### What Would Change in a Real NOC

1. **Internet isolation would be permanent** — no temporary NIC for package installation. All packages would be pre-staged or installed from a local mirror.

2. **Secrets management** — credentials would be in HashiCorp Vault or a cloud secrets manager, not in `.env` files. API keys would be rotated regularly.

3. **Report delivery** — instead of writing to a local folder, reports would be sent to:
   - A ticketing system (ServiceNow, Jira) as incident tickets
   - A Slack/Teams channel for P1/P2 alerts
   - Email for daily summaries
   - The SIEM itself (forwarding agent reports back to Wazuh)

4. **Network enforcement** — the firewall rules would be enforced at the network level (switch ACLs or firewall rules), not just on the VM. Defense in depth.

5. **Redundancy** — two jump boxes in an active-active or active-passive configuration. If one dies, monitoring continues.

6. **Compliance** — the jump box itself would be monitored by the SIEM (unlike this lab design where it IS the monitoring system). All access to the jump box would be logged and audited.

---

## Troubleshooting

### VM can't reach R1 on VLAN 15
- Verify R1 has Fa0/0.15 configured with 10.0.15.1/24
- Verify SW-1 trunk port allows VLAN 15
- Verify the VMware bridge is on the correct physical NIC (the one connected to SW-1)

### UFW blocking needed traffic
- Check `sudo ufw status verbose` to see active rules
- Add rules with `sudo ufw allow out to <IP> port <port> proto <protocol>`
- Test with `curl` or `ping` before enabling the firewall

### AI-Agent can't reach ollama-cloud API
- The VM needs outbound HTTPS to `ollama.com` for the LLM API
- Either add a temporary rule: `sudo ufw allow out to any port 443 proto tcp` (for the API only)
- Or use a local model (Ollama running on the jump box itself — requires more RAM)

### Netmiko SSH to R1 fails
- Verify the legacy crypto parameters match your `netmiko_base.py`
- Test with plain SSH first: `ssh admin@10.0.24.1` (will need legacy crypto options)
- Check that the SSH key is copied to R1: `ssh -i ~/.ssh/monitor_key admin@10.0.24.1`

---

## Related Files

- [[Agent Architecture]] — Architecture concept and rationale
- [[Network Reference]] — Full network documentation
- [[Network Foundry Portfolio]] — Lab portfolio