# SNMP — Simple Network Management Protocol

> **Created:** 2026-07-11
> **Author:** Admin with AI-Agent
> **Purpose:** Reference guide for SNMP concepts, usage in Network Foundry lab, and step-by-step configuration on Cisco devices for Zabbix monitoring

---

## 1. What Is SNMP?

SNMP (Simple Network Management Protocol) is a standard protocol used to collect information from network devices — routers, switches, servers, printers, UPS units, anything on the network. It runs on UDP port 161 (polling) and UDP port 162 (traps/inbound notifications).

Think of SNMP as a universal language for asking network devices questions about their health. Instead of SSHing into every device individually to run `show` commands, a monitoring system like Zabbix sends SNMP queries to all devices on a schedule and collects the answers automatically. The device responds with structured data that the monitoring system can graph, alert on, and display on a dashboard.

---

## 2. SNMP Versions

| Version | Security | Usage |
|---------|----------|-------|
| SNMPv1 | No encryption, community string only (plaintext) | Legacy devices, basic polling |
| SNMPv2c | No encryption, community string only (plaintext) | Most common in labs and small networks |
| SNMPv3 | Encrypted, authenticated (username/password/encryption) | Enterprise production, secure environments |

**Network Foundry uses SNMPv2c** with community string `public` (read-only). This is standard for a lab environment. In production, you'd use SNMPv3 with authentication and encryption.

---

## 3. Key Concepts

### Community String
A community string is SNMP's version of a password. When a monitoring system sends an SNMP query, it includes the community string. The device checks it and responds if it matches. There are two types:

- **RO (Read-Only):** The monitoring system can read data but cannot change anything on the device. This is what we use.
- **RW (Read-Write):** The monitoring system can read AND write configuration to the device. This is dangerous and should rarely be used.

### OIDs (Object Identifiers)
OIDs are the specific data points you can query. They're structured as a hierarchical tree, like a filesystem path. Examples:

| OID | What It Returns |
|-----|-----------------|
| `1.3.6.1.2.1.1.1.0` | System description (device name, OS version) |
| `1.3.6.1.2.1.1.3.0` | System uptime |
| `1.3.6.1.2.1.2.2.1.8.x` | Interface operational status (up/down) for interface x |
| `1.3.6.1.2.1.2.2.1.10.x` | Interface inbound octets (bytes received) for interface x |
| `1.3.6.1.4.1.9.2.1.58.0` | Cisco-specific: CPU utilization (5-second average) |

The `1.3.6.1.4.1.9.*` branch is Cisco's enterprise-specific OID tree. Standard OIDs (system, interfaces, etc.) are under `1.3.6.1.2.1.*`.

### MIBs (Management Information Base)
A MIB is a text file that defines what OIDs mean — it translates the numeric OID into a human-readable name. For example, MIB translates `1.3.6.1.2.1.1.1.0` to `sysDescr`. Zabbix comes with MIBs for most common device types, including Cisco IOS, which is why it can automatically know which OIDs to poll when you apply a Cisco template.

### Traps
Traps are unsolicited notifications sent FROM the device TO the monitoring system on UDP port 162. Instead of the monitoring system asking "is everything okay?", the device proactively sends a message when something happens — interface goes down, CPU spikes, configuration changes. Traps are useful for real-time alerting but are less reliable than polling because they're fire-and-forget (no confirmation that the monitoring system received them).

### Polling
Polling is the monitoring system asking the device for data on a schedule. Zabbix polls every 30-60 seconds by default. Polling is reliable because the monitoring system controls the schedule and can detect if a device stops responding (indicating it's down).

---

## 4. How SNMP Is Used in Network Foundry

Zabbix (running on lab-srv1 at 10.0.24.10) uses SNMP to poll the following lab devices:

| Device | IP | SNMP Community | What Zabbix Monitors |
|--------|-----|----------------|----------------------|
| R1 (Cisco 2650XM) | 10.0.24.1 | public | Interface status, CPU utilization, memory, routing table size, environmental stats |
| SW-1 (Cisco 3750) | 10.0.24.11 | public | Interface status, port utilization, VLAN info, CPU, memory |
| lab-srv1 | 10.0.24.10 | N/A (Zabbix agent) | Local system metrics via Zabbix agent (not SNMP) |

The monitoring flow:
```
Zabbix Server (10.0.24.10)
    |
    |-- SNMP poll (UDP 161) --> R1 (10.0.24.1) --> Returns interface/CPU data
    |
    |-- SNMP poll (UDP 161) --> SW-1 (10.0.24.11) --> Returns interface/port data
    |
    |-- Zabbix Agent (TCP 10050) --> lab-srv1 (localhost) --> Returns local system data
```

Zabbix uses polling (every 30-60 seconds) for real-time data collection and can also receive SNMP traps (UDP 162) for immediate event notifications.

---

## 5. SNMP vs SSH Monitoring

You might wonder why we use SNMP for Zabbix when the AI-Agent NOC agent already SSHes into R1 and SW-1 to run `show` commands. They serve different purposes:

| | SNMP (Zabbix) | SSH (AI-Agent NOC Agent) |
-|----------------|-------------------------|
| Frequency | Every 30-60 seconds | Once daily |
| Data depth | Standardized OIDs (interface, CPU, memory) | Full show command output (routing, OSPF, errors, DHCP) |
| Visual dashboard | Yes — real-time graphs and alerts | No — text reports in Obsidian |
| Analysis | Threshold-based alerting (CPU > 50%, interface down) | AI-reasoned analysis with Tier 1/2 context |
| Learning value | Operational awareness | NOC workflow and incident response training |

They're complementary — Zabbix gives you the live "is anything red?" view, the NOC agent gives you the "what changed and what should I do?" analysis.

---

## 6. Step-by-Step: Configure SNMP on Cisco IOS Devices

### Prerequisites
- SSH access to the Cisco device (R1 or SW-1)
- Privileged EXEC mode access (`enable` password)
- Zabbix server running and reachable from the device

### Step 1: Access the Device

SSH into the device. For R1 with legacy crypto:

```bash
ssh -o KexAlgorithms=+diffie-hellman-group1-sha1 \
    -o HostKeyAlgorithms=+ssh-rsa \
    -o PubkeyAcceptedKeyTypes=+ssh-rsa \
    -o Ciphers=aes128-cbc \
    -o MACs=hmac-sha1 \
    admin@10.0.24.1
```

Or use the WSL alias:
```bash
r1ssh
```

Enter privileged EXEC mode:
```
enable
```
Password: `[REDACTED]`

### Step 2: Enter Configuration Mode

```
configure terminal
```

### Step 3: Set the SNMP Community String

```
snmp-server community public RO
```

This creates a read-only community string named `public`. Any SNMP client that sends queries with community `public` will receive read-only access to the device's SNMP data.

**Optional — restrict SNMP access to specific hosts:**
```
snmp-server community public RO 10
```
This applies standard ACL 10 to restrict which IPs can send SNMP queries. You'd then create the ACL:
```
access-list 10 permit 10.0.24.10
access-list 10 deny any
```
This limits SNMP access to only the Zabbix server (10.0.24.10). Recommended for production, optional for the lab.

### Step 4: Set SNMP Contact and Location (Optional but Good Practice)

```
snmp-server contact "Admin - admin@lab.local"
snmp-server location "Network Foundry Lab - Home Lab Rack"
```

These values are returned when someone queries the system contact (`1.3.6.1.2.1.1.4.0`) and system location (`1.3.6.1.2.1.1.6.0`) OIDs. Useful for inventory management in larger environments.

### Step 5: Enable SNMP Traps

```
snmp-server enable traps
```

This enables the device to send SNMP traps (notifications) to a monitoring server when events occur. By default, this enables all trap types. You can selectively enable specific traps:

```
snmp-server enable traps snmp authentication linkdown linkup coldstart
snmp-server enable traps config
snmp-server enable traps cpu threshold
```

For the lab, `snmp-server enable traps` (all) is fine.

### Step 6: Configure the Trap Destination

```
snmp-server host 10.0.24.10 version 2c public
```

This tells the device to send traps to the Zabbix server (10.0.24.10) using SNMPv2c with community string `public`.

### Step 7: Exit and Save

```
end
write memory
```

### Step 8: Verify SNMP Is Working

From lab-srv1 or any Linux machine on the lab network:

```bash
# Test basic SNMP connectivity — should return the system description
snmpwalk -v 2c -c public 10.0.24.1 1.3.6.1.2.1.1.1.0

# Expected output for R1:
# SNMPv2-MIB::sysDescr.0 = STRING: Cisco IOS Software, 2650XM Software (C2600-ADVSECURITYK9-M), Version 12.4(15)T4

# Test interface status
snmpwalk -v 2c -c public 10.0.24.1 1.3.6.1.2.1.2.2.1.8

# Test CPU utilization (Cisco-specific OID)
snmpwalk -v 2c -c public 10.0.24.1 1.3.6.1.4.1.9.2.1.58.0
```

If you get `Timeout: No Response`, check:
- The community string is correct (`public`)
- The device is reachable (`ping 10.0.24.1`)
- The SNMP service is running on the device (`show running-config | include snmp`)
- No ACL is blocking UDP port 161

---

## 7. Repeat for SW-1

SW-1 (Cisco 3750) uses the same SNMP configuration commands. SSH into SW-1 and repeat Steps 2-7:

```
enable
configure terminal
snmp-server community public RO
snmp-server contact "Admin - admin@lab.local"
snmp-server location "Network Foundry Lab - Core Switch"
snmp-server enable traps
snmp-server host 10.0.24.10 version 2c public
end
write memory
```

Verify from lab-srv1:
```bash
snmpwalk -v 2c -c public 10.0.24.11 1.3.6.1.2.1.1.1.0
```

---

## 8. Adding Devices to Zabbix

Once SNMP is responding from both devices, add them in the Zabbix web UI:

1. Open `http://10.0.24.10/zabbix` (login: Admin / [REDACTED])
2. Navigate to **Configuration → Hosts → Create host**
3. For each device, enter:
   - **Host name:** R1 (or SW-1)
   - **Groups:** Select or create "Network Foundry Devices"
   - **Interfaces:** Add SNMP interface with IP address (10.0.24.1 or 10.0.24.11)
   - **SNMP community:** `{$SNMP_COMMUNITY}` = `public`
4. Under **Templates**, link the appropriate template:
   - R1: **Template Net Cisco IOS SNMP** (generic Cisco IOS monitoring)
   - SW-1: **Template Net Cisco IOS SNMP** (same template works for 3750)
5. Click **Add**

Within 30-60 seconds, Zabbix should start populating data for the new hosts. Check **Monitoring → Latest Data** to see incoming values.

---

## 9. Troubleshooting SNMP

| Problem | Likely Cause | Fix |
|---------|-------------|-----|
| `Timeout: No Response` | SNMP not enabled on device | Run `show running-config \| include snmp` on the device |
| `Timeout: No Response` | ACL blocking UDP 161 | Check for ACLs on the device interface |
| `Timeout: No Response` | Wrong community string | Verify community string matches between device and query |
| Zabbix shows "SNMP not available" | Firewall blocking UDP 161 | Check UFW on lab-srv1: `sudo ufw allow from 10.0.24.1 to any port 161 proto udp` |
| Zabbix shows no data | Template not linked or wrong OID | Verify template is linked and device responds to snmpwalk |
| Partial data only | Some OIDs not supported by device | Cisco 2650XM (IOS 12.4) may not support all modern OIDs — use the generic Cisco IOS template |

---

## 10. Security Considerations

### Lab Environment (Current)
- SNMPv2c with community string `public` is acceptable
- No ACL restriction (any device on the lab network can query SNMP)
- Traps sent unencrypted

### Production Environment (Future)
- Use SNMPv3 with authentication and encryption:
  ```
  snmp-server group LAB v3 priv read LAB-READ
  snmp-server user zabbix LAB v3 auth sha <auth-password> priv aes 128 <priv-password>
  ```
- Restrict SNMP access with ACLs to only the monitoring server
- Use a non-default community string (not `public`)
- Disable SNMPv1 and SNMPv2c entirely

---

## Related Files

- [[Network Reference]] — Full network documentation
- [[Zabbix Installation]] — Zabbix server installation guide
- [[Network Foundry Portfolio]] — Lab portfolio