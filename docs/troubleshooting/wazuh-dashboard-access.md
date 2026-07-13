# Wazuh Dashboard Access — Troubleshooting Log

> **Date:** 2026-07-09
> **Resolved By:** Admin with AI-Agent
> **Symptoms:** Wazuh dashboard inaccessible from desktop PC browser; "This site can't be reached" when navigating to the Wazuh manager IP
> **Root Cause:** Windows network adapter classified as "Public" profile — Windows Firewall blocked browser HTTPS connections to the lab network

---

## 1. Initial State

After powering on the lab, the Wazuh dashboard was inaccessible from the desktop PC's browser (Brave and Edge). All Wazuh services were confirmed running:

```bash
systemctl status wazuh-manager      # active
systemctl status wazuh-indexer     # active
systemctl status wazuh-dashboard   # active
```

Restarting all three services did not resolve the issue. The browser still could not reach the dashboard.

---

## 2. Troubleshooting Steps

### Step 1: Verify Infrastructure Reachability

Ran ping tests from WSL on the laptop to all lab devices:

```
PING 10.0.24.11 (SW-1)         → ✅ 0% packet loss
PING 10.0.24.10 (lab-srv1)  → ✅ 0% packet loss
PING 10.0.24.1  (R1)           → ✅ 0% packet loss
PING 10.0.24.13 (Wazuh)        → ✅ 0% packet loss
PING 10.0.24.14 (GNS3 VM)      → ✅ 0% packet loss
PING 10.0.24.120 (desktop host) → ❌ 100% packet loss (Destination Host Unreachable)
```

**Finding:** All VMs and network devices were reachable from WSL, but the desktop host OS itself was unreachable. The VMs bridge through the host's NIC at Layer 2 (bypassing the host OS network stack), which is why the VMs were reachable even though the host was not.

### Step 2: Verify Wazuh Services on the Correct IP

Ran port scans from lab-srv1 to identify what was actually listening on each lab IP:

```bash
# Port scan 10.0.24.13
Port 443: OPEN     ← Wazuh dashboard (HTTPS)
Port 80:  closed
Port 5601: closed   ← Documented port, but NOT where the dashboard is
Port 22:  OPEN

# Port scan 10.0.24.14
Port 80:  OPEN     ← GNS3 Web UI (not Wazuh)
Port 443: closed
Port 22:  OPEN
```

**Finding:** The Wazuh dashboard had moved from its documented location (`10.0.24.14:5601`) to `https://10.0.24.13` (port 443). The GNS3 VM had taken over `10.0.24.14`. The documentation (Network-Reference.md, last updated 2026-05-14) had the old IP assignments.

**Action:** Updated mental model — Wazuh dashboard is at `https://10.0.24.13`, not `https://10.0.24.14:5601`.

### Step 3: Verify Wazuh Dashboard Is Actually Serving

Ran curl from lab-srv1 to confirm the dashboard was serving content:

```bash
curl -sk --connect-timeout 5 -L https://10.0.24.13
# HTTP 302 → redirect to /app/login
# <title>Wazuh</title>
```

**Finding:** The Wazuh dashboard was fully operational and serving the login page. The problem was not a Wazuh service issue — it was a network access issue between the desktop browser and the Wazuh VM.

### Step 4: Verify Windows Network Configuration

Checked the Windows host's network adapters and routing table via PowerShell:

```powershell
Get-NetAdapter
# Name: Ethernet (Realtek PCIe GbE Family Controller)
# Status: Up
# IP: 10.0.24.15 (later changed to 10.0.24.16)
```

```powershell
Get-NetRoute -AddressFamily IPv4 | Where-Object { $_.DestinationPrefix -like '10.0.*' }
# DestinationPrefix: 10.0.24.0/21
# NextHop: 0.0.0.0 (directly connected)
# InterfaceAlias: Ethernet
```

**Finding:** The routing table showed a valid route to `10.0.24.0/21` through the Ethernet adapter. The path existed at the network layer.

### Step 5: Test Windows TCP Connectivity

Ran a TCP connection test from the Windows side directly:

```powershell
Test-NetConnection -ComputerName 10.0.24.13 -Port 443
# TcpTestSucceeded: True (intermittently — timed out on subsequent attempts)
```

```powershell
# PowerShell Invoke-WebRequest
try {
    $r = Invoke-WebRequest -Uri 'https://10.0.24.13' -TimeoutSec 8 -UseBasicParsing
} catch {
    # Error: "The underlying connection was closed: Could not establish trust
    #         relationship for the SSL/TLS secure channel."
}
```

**Finding:** Windows could establish a TCP connection to port 443, but the TLS handshake was failing. However, browsers were showing "This site can't be reached" rather than a certificate warning — suggesting the connection was being blocked before the TLS handshake could even begin in some cases.

### Step 6: Check Windows Network Profile (Root Cause)

Checked the Windows network profile classification for the lab adapter:

```powershell
Get-NetConnectionProfile -InterfaceAlias "Server VLAN24"
# Name: Network
# InterfaceAlias: Server VLAN24
# NetworkCategory: Public    ← ROOT CAUSE
```

**Finding:** The lab network adapter ("Server VLAN24") was classified as **Public** network. Windows Firewall's Public profile is the most restrictive — it blocks most outbound connections to local network devices by default. This was preventing the browser from reaching the Wazuh dashboard even though the network path, routing, and Wazuh services were all functional.

### Step 7: Verify Desktop Host Reachability

Confirmed the desktop host at `10.0.24.120` was unreachable from all devices:

```
Ping from laptop WSL:       10.0.24.120 → ❌ Destination Host Unreachable
Ping from lab-srv1:      10.0.24.120 → ❌ 100% packet loss
```

**Finding:** The desktop host OS does not have its NIC configured on the lab network. The VMs (Wazuh, GNS3, lab-srv1) bridge through the host's physical NIC at Layer 2, bypassing the host OS network stack entirely. This is why the VMs are reachable but the host itself is not.

---

## 3. Solution

### Fix: Change Windows Network Profile from Public to Private

On the affected machine (desktop PC), open an **admin PowerShell** and run:

```powershell
Set-NetConnectionProfile -InterfaceAlias "Server VLAN24" -NetworkCategory Private
```

This reclassifies the lab network adapter from the restrictive Public profile to the Private profile, which allows outbound browser connections to local network devices.

After running this command, `https://10.0.24.13` loaded correctly in the browser and the Wazuh login page appeared.

### Why This Worked

- **Public profile:** Windows Firewall blocks most inbound and some outbound connections, treating the network as untrusted (e.g., a coffee shop Wi-Fi). This blocked the browser's HTTPS connection to the Wazuh dashboard.
- **Private profile:** Windows Firewall allows normal local network communication. This is the correct classification for a trusted lab network that you control.
- The VMs were always reachable from WSL because WSL2's networking stack routes through the Hyper-V virtual switch, which has different firewall rules than the Windows browser/HTTP stack.

---

## 4. Additional Issues Discovered

### 4.1 IP Address Assignments Changed

The lab IP assignments have shifted since the documentation was last updated (2026-05-14). Current live state:

| Device | Documented IP | Actual IP | Notes |
|--------|---------------|-----------|-------|
| Wazuh Dashboard | 10.0.24.14:5601 | **10.0.24.13:443** | Moved to HTTPS on port 443 |
| GNS3 VM | 10.0.24.13 | **10.0.24.14** | Now serving GNS3 Web UI on port 80 |
| Desktop Host | 10.0.24.120 | **Unreachable** | Host OS NIC not configured on lab network |

### 4.2 Desktop Host Not on Lab Network

The desktop host at `10.0.24.120` is unreachable from all lab devices. The VMs work because they bridge at Layer 2 through the host's physical NIC, but the host OS itself does not have a configured IP on the lab network. This should be addressed if remote management of the desktop from the laptop is needed.

### 4.3 WSL Mirrored Networking IP Conflict

During troubleshooting, the Windows Ethernet adapter showed a "Duplicate" IP address flag when set to `10.0.24.15`. This was caused by WSL2's `networkingMode=mirrored` creating a virtual copy of the physical adapter with the same IP. Resolved by changing the Windows adapter to `10.0.24.16` to avoid the conflict. However, WSL continued using `.15` internally without issue.

### 4.4 Wazuh API Credentials

The Wazuh Manager SSH alias in the documentation uses:
```bash
sshpass -p "[REDACTED]" ssh wazuh-user@10.0.24.14
```
This should be updated to reflect the new IP (`10.0.24.13` for the dashboard, and the Wazuh Manager's SSH endpoint should be verified separately).

---

## 5. Verification

After applying the fix, the following was confirmed:

- ✅ Wazuh dashboard accessible at `https://10.0.24.13` from the desktop PC browser
- ✅ All Wazuh services running (wazuh-manager, wazuh-indexer, wazuh-dashboard)
- ✅ All lab devices reachable from WSL on the laptop (SW-1, R1, lab-srv1, Wazuh, GNS3)
- ✅ Samba AD DC operational on lab-srv1 (10.0.24.10)
- ✅ AI-Agent SSH access to lab-srv1 working (ai-agent@10.0.24.10, key auth)

---

## 6. Recommendations

1. **Update Network-Reference.md** with the current IP assignments (Wazuh at .13:443, GNS3 at .14)
2. **Set the desktop host's NIC** to a static IP on the lab network (10.0.24.120/21, gw 10.0.24.1) if remote management is needed
3. **Ensure the "Server VLAN24" adapter** stays on the Private network profile — Windows may reset this if the adapter is removed/re-added or drivers are updated
4. **Install the Wazuh self-signed certificate** into the Windows Trusted Root store on machines that need browser access (see cert installation script in this doc)
5. **Document the Wazuh dashboard URL** as `https://10.0.24.13` (no port number needed — it's on standard HTTPS 443)

---

## Related Files

- [[Network Reference]] — Full network documentation (needs IP assignment update)
- [[Wazuh Agent Installation]] — Wazuh agent installation guide
- [[Network Foundry Portfolio]] — Lab portfolio overview
- [[LAB-SRV1]] — Server SOP