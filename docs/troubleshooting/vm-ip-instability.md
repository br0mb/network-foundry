# GNS3 VM IP Address Instability — Troubleshooting Log

> **Date:** 2026-07-10
> **Resolved By:** Admin with AI-Agent
> **Symptoms:** GNS3 VM IP address changing on every boot, swapping IPs with Wazuh Manager, grabbing multiple DHCP leases
> **Root Cause:** Multiple netplan configuration files in `/etc/netplan/` with conflicting DHCP/static settings, reinforced by cloud-init regenerating configs on boot

---

## 1. Problem Description

The GNS3 VM (and Wazuh Manager VM) were receiving dynamic IP addresses via DHCP from R1's VLAN 24 pool. On each boot, whichever VM started first would grab the next available DHCP address. This caused:

- GNS3 and Wazuh swapping IPs between `.13` and `.14` on every reboot
- Monitoring scripts, firewall rules, and documentation pointing at the wrong IPs after each restart
- Wazuh agent on lab-srv1 losing connection to the Wazuh Manager when the manager's IP changed
- IP conflicts with the Windows host NIC

---

## 2. Investigation

### Step 1: Check R1 ARP and DHCP Bindings

```
R1# show ip arp | include 10.0.24
Internet  10.0.24.12              0   000c.29b2.c4af  ARPA   FastEthernet0/0.24
Internet  10.0.24.13             16   000c.29b2.c4af  ARPA   FastEthernet0/0.24
Internet  10.0.24.14             33   000c.2917.6607  ARPA   FastEthernet0/0.24
```

**Finding:** GNS3 VM (MAC `000c.29b2.c4af`) was holding TWO DHCP leases — `.12` and `.13` simultaneously. lab-srv1 (MAC `000c.2917.6607`) had a static IP at `.10` but was ALSO grabbing a DHCP lease at `.14`.

### Step 2: Check GNS3 VM Network Configuration

```bash
gns3@gns3vm:~$ sudo netplan get
network:
  version: 2
  renderer: networkd
  ethernets:
    eth0:
      dhcp-identifier: "mac"
      dhcp4: true
    eth1:
      dhcp-identifier: "mac"
      dhcp4: true
    ...
```

**Finding:** The active netplan config showed eth0 on DHCP, despite a static IP config file being written. Multiple netplan config files were present:

```bash
gns3@gns3vm:~$ ls /etc/netplan/
00-installer-config.yaml
01-netcfg.yaml                    ← Our static config (10.0.24.14/21)
80_gns3vm_default_netcfg.yaml     ← GNS3's default: eth0 DHCP=true (OVERRIDING)
90_gns3vm_static_netcfg.yaml      ← Commented out static config
```

**Root Cause Identified:** Netplan merges ALL `.yaml` files in `/etc/netplan/`. The `80_gns3vm_default_netcfg.yaml` file (shipped with the GNS3 VM appliance) was setting eth0 to DHCP. Since netplan files are processed in alphabetical/numeric order, `80_*` overrides `01_*`. Our static config in `01-netcfg.yaml` was being overridden by the GNS3 default config in `80_gns3vm_default_netcfg.yaml`.

Additionally, cloud-init was regenerating netplan configs on every boot, meaning any manual edits to netplan files would be overwritten on restart.

### Step 3: Verify the Double IP

```bash
gns3@gns3vm:~$ ip addr show eth0 | grep inet
    inet 10.0.24.14/21 brd 10.0.31.255 scope global eth0
    inet 10.0.24.13/21 metric 100 brd 10.0.31.255 scope global secondary dynamic eth0
```

**Finding:** eth0 had the static `.14` (from our config) AND a dynamic `.13` (from the DHCP lease granted by the `80_*` config file). Two IPs on one interface — the DHCP lease was persistent and survived reboots.

---

## 3. Solution

### Step 1: Disable Cloud-Init Network Regeneration

```bash
sudo touch /etc/cloud/cloud-init.disabled
```

This prevents cloud-init from regenerating netplan config files on every boot. Without this, any netplan edits would be overwritten on restart.

### Step 2: Write Static IP Config

```bash
sudo tee /etc/netplan/01-netcfg.yaml > /dev/null << 'EOF'
network:
  version: 2
  renderer: networkd
  ethernets:
    eth0:
      dhcp4: false
      addresses:
        - 10.0.24.14/21
      routes:
        - to: default
          via: 10.0.24.1
      nameservers:
        addresses:
          - 10.0.24.10
    eth1:
      dhcp4: true
    eth2:
      optional: true
      dhcp4: true
    eth3:
      optional: true
      dhcp4: true
    eth4:
      optional: true
      dhcp4: true
    eth5:
      optional: true
      dhcp4: true
    eth6:
      optional: true
      dhcp4: true
    eth7:
      optional: true
      dhcp4: true
    eth8:
      optional: true
      dhcp4: true
EOF
```

**Note:** eth1-eth8 are kept on DHCP because GNS3 uses these interfaces for simulated network topologies. Only eth0 (the management interface) needs a static IP.

### Step 3: Disable Conflicting Netplan Config Files

```bash
sudo mv /etc/netplan/80_gns3vm_default_netcfg.yaml /etc/netplan/80_gns3vm_default_netcfg.yaml.bak
sudo mv /etc/netplan/90_gns3vm_static_netcfg.yaml /etc/netplan/90_gns3vm_static_netcfg.yaml.bak
```

Renaming the files to `.bak` prevents netplan from loading them. This stops the GNS3 default DHCP config from overriding our static config.

### Step 4: Apply and Verify

```bash
sudo netplan apply
ip addr show eth0 | grep inet
```

**Result:**
```
inet 10.0.24.14/21 brd 10.0.31.255 scope global eth0
```

Only one IP — the static `.14`. The dynamic `.13` lease was released.

### Step 5: Reboot Test

Rebooted the VM and verified the IP persisted:

```
IP: 10.0.24.14
10.0.24.13 PORT: 80
```

The GNS3 boot screen shows `.14` as the primary IP and `.13` as the web UI port reference (this is a GNS3 display convention, not a second IP). SSH access confirmed at `gns3@10.0.24.14`.

---

## 4. R1 DHCP Configuration

To prevent other devices from grabbing the reserved IPs, the following DHCP exclusion was added to R1:

```
R1(config)# ip dhcp excluded-address 10.0.24.13 10.0.24.15
```

This excludes `.13` through `.15` from the DHCP pool, protecting:
- `10.0.24.13` — Wazuh Manager (static)
- `10.0.24.14` — GNS3 VM (static)
- `10.0.24.15` — Windows host NIC (static, planned)

---

## 5. Same Fix Applied to Wazuh Manager VM

The Wazuh Manager VM (Amazon Linux 2023) had the same cloud-init + netplan issue. The same fix was applied:

```bash
sudo touch /etc/cloud/cloud-init.disabled

sudo tee /etc/netplan/01-netcfg.yaml > /dev/null << 'EOF'
network:
  version: 2
  renderer: networkd
  ethernets:
    eth0:
      dhcp4: false
      addresses:
        - 10.0.24.13/21
      routes:
        - to: default
          via: 10.0.24.1
      nameservers:
        addresses:
          - 10.0.24.10
EOF

# Rename any conflicting netplan files
sudo mv /etc/netplan/WHATEVER.yaml /etc/netplan/WHATEVER.yaml.bak

sudo netplan apply
sudo reboot
```

---

## 6. Lessons Learned

### Netplan File Merging
Netplan merges ALL `.yaml` files in `/etc/netplan/`. Files are processed in alphabetical/numeric order — higher-numbered files override lower-numbered ones for the same interface. If two files both configure eth0, the last one wins. This means adding a new netplan file does NOT override an existing one — you must disable or rename the old file.

### Cloud-Init Network Regeneration
Cloud-init regenerates netplan config files on every boot from its own templates. Any manual edits to netplan files will be overwritten on restart unless cloud-init is disabled with `sudo touch /etc/cloud/cloud-init.disabled`. This is the most common reason "I set a static IP but it reverted after reboot."

### GNS3 VM Appliance Defaults
The GNS3 VM appliance ships with its own netplan config (`80_gns3vm_default_netcfg.yaml`) that sets eth0 to DHCP. This file overrides any custom config because of its higher numeric prefix. Always check for and disable this file when setting a static IP on a GNS3 VM.

### DHCP Double-Lease Problem
When a VM has both a static IP and an active DHCP client, it will hold two IPs on the same interface — the static IP from netplan and the dynamic IP from the DHCP lease. The DHCP lease persists until it expires or is released. Disabling DHCP in the netplan config and renaming conflicting netplan files resolves this.

---

## 7. Final Static IP Assignments

| Device | Static IP | MAC Address | Method |
|--------|-----------|-------------|--------|
| lab-srv1 | 10.0.24.10/21 | 00:0c:29:17:66:07 | Already static (no change needed) |
| Wazuh Manager | 10.0.24.13/21 | 00:0c:29:21:59:cd | Netplan static + cloud-init disabled |
| GNS3 VM | 10.0.24.14/21 | 00:0c:29:b2:c4:af | Netplan static + cloud-init disabled + default config renamed |
| Windows NIC | 10.0.24.15/21 | b0:25:aa:5d:e3:30 | Windows adapter properties (planned) |

---

## Related Files

- [[Network Reference]] — Full network documentation
- [[Wazuh Dashboard Access]] — Wazuh dashboard troubleshooting (Windows firewall fix)
- [[Network Foundry Portfolio]] — Lab portfolio