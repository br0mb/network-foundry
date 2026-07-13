# DNS Records for Lab Services — Setup Log

> **Date:** 2026-07-11
> **Resolved By:** Admin with AI-Agent
> **Goal:** Create friendly DNS names for lab services (wazuh.lab.local, zabbix.lab.local, gns3.lab.local) so they can be accessed by name instead of IP in the browser
> **Status:** DNS records created successfully on Samba DNS server, but not resolving from client machines yet

---

## 1. Goal

Instead of accessing lab services by IP address (`https://10.0.24.13`), create DNS records on the Samba AD DC DNS server so they can be accessed by hostname:

| DNS Name | IP | Service |
|----------|-----|---------|
| `wazuh.lab.local` | 10.0.24.13 | Wazuh dashboard (HTTPS 443) |
| `zabbix.lab.local` | 10.0.24.10 | Zabbix monitoring (HTTP 80) |
| `gns3.lab.local` | 10.0.24.14 | GNS3 Web UI (HTTP 80) |

---

## 2. Prerequisites

- Samba AD DC running on lab-srv1 (10.0.24.10) with DNS backend
- Domain: lab.local
- DNS server must be set to 10.0.24.10 on the client machine's network adapter

---

## 3. Troubleshooting Steps Taken

### Step 1: Attempt samba-tool dns add (Failed — Authentication)

```bash
ssh ai-agent@10.0.24.10
sudo samba-tool dns add 127.0.0.1 lab.local wazuh A 10.0.24.13
```

**Error:**
```
Failed to bind to uuid 50abc2a4-574d-40b3-9d66-ee4fd5fba076
NT_STATUS_LOGON_FAILURE
ERROR: Connecting to DNS RPC server 127.0.0.1 failed with (3221225581, 'The attempted logon is invalid.')
```

**Cause:** The Samba DNS RPC server requires authentication. The `ai-agent` account doesn't have DNS admin rights by default.

### Step 2: Attempt with Administrator Credentials (Failed — Same Error)

```bash
sudo samba-tool dns add 127.0.0.1 lab.local wazuh A 10.0.24.13 \
  -U "LAB\administrator%[REDACTED]"
```

**Same error.** The `samba-tool dns add` command requires Kerberos authentication, not NTLM.

### Step 3: Attempt nsupdate with GSSAPI (Failed — No Kerberos Ticket)

```bash
sudo nsupdate -g << 'EOF'
server 127.0.0.1
zone lab.local
update add wazuh.lab.local 86400 A 10.0.24.13
send
EOF
```

**Error:**
```
tkey query failed: GSSAPI error: Major = No credentials were supplied
```

**Cause:** No Kerberos ticket exists. Need to authenticate with `kinit` first.

### Step 4: Attempt kinit (Failed — Bad krb5.conf)

```bash
echo "[REDACTED]" | kinit administrator@LAB.LOCAL
```

**Error:**
```
kinit: Cannot find KDC for realm "LAB.LOCAL" while getting initial credentials
```

**Cause:** The `/etc/krb5.conf` file was still the default MIT Kerberos config from the Ubuntu install. It had no entry for the LAB.LOCAL realm.

### Step 5: Fix krb5.conf (First Attempt — Wrong KDC Address)

```bash
sudo tee /etc/krb5.conf > /dev/null << 'EOF'
[libdefaults]
    default_realm = LAB.LOCAL
    dns_lookup_realm = false
    dns_lookup_kdc = true

[realms]
    LAB.LOCAL = {
        kdc = lab-srv1.lab.local
        admin_server = lab-srv1.lab.local
    }

[domain_realm]
    .lab.local = LAB.LOCAL
    lab.local = LAB.LOCAL
EOF
```

**Error:**
```
kinit: Resource temporarily unavailable while getting initial credentials
```

**Cause:** The KDC (Kerberos Key Distribution Center) on the Samba AD DC is listening on `127.0.0.1:88` only, not on the external interface. Using `lab-srv1.lab.local` as the KDC address failed because the DNS resolution created a circular dependency (DNS needs Kerberos, Kerberos needs DNS).

### Step 6: Fix krb5.conf (Second Attempt — Use 127.0.0.1)

```bash
sudo tee /etc/krb5.conf > /dev/null << 'EOF'
[libdefaults]
    default_realm = LAB.LOCAL
    dns_lookup_realm = false
    dns_lookup_kdc = false

[realms]
    LAB.LOCAL = {
        kdc = 127.0.0.1
        admin_server = 127.0.0.1
    }

[domain_realm]
    .lab.local = LAB.LOCAL
    lab.local = LAB.LOCAL
EOF
```

### Step 7: Attempt kinit Again (Failed — Password Expired)

```bash
echo "[REDACTED]" | kinit administrator@LAB.LOCAL
```

**Error:**
```
Password for administrator@LAB.LOCAL:
Password expired. You must change it now.
Enter new password:
kinit: Cannot read password while getting initial credentials
```

**Root Cause Found:** The Administrator domain account password had expired. This was the underlying cause of ALL authentication failures throughout this process. Every attempt to authenticate to the Samba DNS RPC server failed because the Administrator password was expired.

### Step 8: Reset Administrator Password and Disable Expiry

```bash
# Reset the password
sudo samba-tool user setpassword administrator --newpassword="[REDACTED]"

# Disable password expiry so this doesn't happen again
sudo samba-tool user setexpiry administrator --noexpiry
```

### Step 9: kinit Works

```bash
echo "[REDACTED]" | kinit administrator@LAB.LOCAL
klist
```

**Output:**
```
Ticket cache: FILE:/tmp/krb5cc_1001
Default principal: administrator@LAB.LOCAL

Valid starting       Expires              Service principal
07/11/2026 21:58:18  07/12/2026 07:58:18  krbtgt/LAB.LOCAL@LAB.LOCAL
```

### Step 10: Add DNS Records (Success)

```bash
# Add Wazuh
sudo samba-tool dns add 127.0.0.1 lab.local wazuh A 10.0.24.13 \
  -U "LAB\administrator%[REDACTED]" --option="client use kerberos = no"

# Add Zabbix
sudo samba-tool dns add 127.0.0.1 lab.local zabbix A 10.0.24.10 \
  -U "LAB\administrator%[REDACTED]" --option="client use kerberos = no"

# Add GNS3
sudo samba-tool dns add 127.0.0.1 lab.local gns3 A 10.0.24.14 \
  -U "LAB\administrator%[REDACTED]" --option="client use kerberos = no"
```

All three returned: `Record added successfully`

### Step 11: Verify Records on the Server

```bash
dig @127.0.0.1 wazuh.lab.local A +short
dig @127.0.0.1 zabbix.lab.local A +short
dig @127.0.0.1 gns3.lab.local A +short
```

**Output:**
```
10.0.24.13
10.0.24.10
10.0.24.14
```

DNS records are confirmed working on the Samba DNS server itself. Queries from `127.0.0.1` resolve correctly.

---

## 4. Current Issue — DNS Not Resolving from Client Machines

The DNS records were created successfully on the Samba DNS server and verify correctly when querying `127.0.0.1` from lab-srv1 itself. However, the DNS names are not resolving from client machines (laptop browser, WSL).

### Possible Causes to Investigate

1. **Client DNS server setting** — The laptop's network adapter DNS must be set to `10.0.24.10` (the Samba DC). If it's set to `8.8.8.8` or the Xfinity router, it won't know about `lab.local` records. Check with:
   ```powershell
   Get-DnsClientServerAddress -InterfaceAlias "Server VLAN24"
   ```

2. **DNS suffix search order** — The client may not be appending `lab.local` to single-label queries. The full FQDN (`wazuh.lab.local`) should work without suffix search, but verify the client is using the full name.

3. **Samba DNS listening interface** — The Samba DNS server may be listening on `ens33` and `lo` only (per the Samba config `interfaces = lo ens33`). If the client is on a different VLAN or the DNS query is being routed through R1, it should still work since R1 forwards DNS to the Samba DC.

4. **DNS cache** — The client machine may have cached a negative response. Flush with:
   ```powershell
   ipconfig /flushdns
   ```

5. **R1 DNS forwarding** — R1 forwards DNS to the Samba DC (10.0.24.10), so any client using R1 as DNS should also resolve. Verify R1's DNS config:
   ```
   show running-config | include name-server
   ```

### Verification Commands

From the laptop (Windows PowerShell):
```powershell
# Check which DNS server the adapter is using
Get-DnsClientServerAddress -InterfaceAlias "Server VLAN24"

# Flush DNS cache
ipconfig /flushdns

# Test resolution
Resolve-DnsName wazuh.lab.local
nslookup wazuh.lab.local 10.0.24.10
```

From WSL:
```bash
# Test DNS resolution
nslookup wazuh.lab.local 10.0.24.10
dig @10.0.24.10 wazuh.lab.local A +short
```

From R1:
```
ping wazuh.lab.local
```

---

## 5. Fixes Applied During This Process

### Fix 1: krb5.conf Updated

The `/etc/krb5.conf` on lab-srv1 was the default MIT Kerberos config with no LAB.LOCAL realm entry. Updated to:

```ini
[libdefaults]
    default_realm = LAB.LOCAL
    dns_lookup_realm = false
    dns_lookup_kdc = false

[realms]
    LAB.LOCAL = {
        kdc = 127.0.0.1
        admin_server = 127.0.0.1
    }

[domain_realm]
    .lab.local = LAB.LOCAL
    lab.local = LAB.LOCAL
```

**Note:** The KDC is set to `127.0.0.1` because the Samba AD DC's Kerberos KDC listens on localhost only. Using the hostname `lab-srv1.lab.local` created a circular dependency (DNS needs Kerberos, Kerberos needs DNS).

### Fix 2: Administrator Password Reset

The Administrator domain account password had expired, which was the root cause of all authentication failures. Reset with:

```bash
sudo samba-tool user setpassword administrator --newpassword="[REDACTED]"
sudo samba-tool user setexpiry administrator --noexpiry
```

**Note:** You should consider disabling password expiry on all lab domain accounts to prevent this from happening again:
```bash
sudo samba-tool user setexpiry user --noexpiry
sudo samba-tool user setexpiry admin --noexpiry
sudo samba-tool user setexpiry ai-agent --noexpiry
```

### Fix 3: DNS Records Created

Three A records added to the lab.local DNS zone:

```bash
sudo samba-tool dns add 127.0.0.1 lab.local wazuh A 10.0.24.13 -U "LAB\administrator%[REDACTED]" --option="client use kerberos = no"
sudo samba-tool dns add 127.0.0.1 lab.local zabbix A 10.0.24.10 -U "LAB\administrator%[REDACTED]" --option="client use kerberos = no"
sudo samba-tool dns add 127.0.0.1 lab.local gns3 A 10.0.24.14 -U "LAB\administrator%[REDACTED]" --option="client use kerberos = no"
```

---

## 6. To Add More DNS Records in the Future

Once Kerberos is working (kinit succeeds), adding new DNS records is a single command:

```bash
ssh ai-agent@10.0.24.10
echo "[REDACTED]" | kinit administrator@LAB.LOCAL
sudo samba-tool dns add 127.0.0.1 lab.local <hostname> A <ip-address> -U "LAB\administrator%[REDACTED]" --option="client use kerberos = no"
```

To verify:
```bash
dig @127.0.0.1 <hostname>.lab.local A +short
```

To delete a record:
```bash
sudo samba-tool dns delete 127.0.0.1 lab.local <hostname> A <ip-address> -U "LAB\administrator%[REDACTED]" --option="client use kerberos = no"
```

---

## 7. Lessons Learned

### Kerberos is Required for Samba DNS Management
The `samba-tool dns add` command requires Kerberos authentication to the Samba DNS RPC server. NTLM authentication doesn't work for DNS operations even with the `--option="client use kerberos = no"` flag — that flag is needed to avoid a Kerberos *lookup* error, but the credentials still need to be valid.

### KDC on Localhost
The Samba AD DC's Kerberos KDC listens on `127.0.0.1:88` only, not on the external interface. The `krb5.conf` must point to `127.0.0.1` as the KDC, not the server's hostname or external IP. Using the hostname creates a circular dependency — DNS resolution needs Kerberos, and Kerberos needs to reach the KDC which needs DNS to resolve the hostname.

### Password Expiry Breaks Everything Silently
The Administrator password had expired, but the error messages didn't say "password expired" — they said "logon failure" and "authentication invalid." This is because the Samba DNS RPC server rejects expired passwords with a generic authentication failure error rather than a specific "password expired" message. The only way to discover the expiry was to attempt `kinit` directly, which gave the specific "Password expired" error.

### DNS Verification Hierarchy
When troubleshooting DNS, always verify from the inside out:
1. Query the DNS server from itself (`dig @127.0.0.1`) — confirms the record exists
2. Query the DNS server from a client (`dig @10.0.24.10`) — confirms the server is responding to external queries
3. Query using the client's configured DNS (`nslookup wazuh.lab.local`) — confirms the client is using the right DNS server
4. Test in the browser — confirms end-to-end resolution + service availability

---

## Related Files

- [[Network Reference]] — Full network documentation
- [[Wazuh Dashboard Access]] — Wazuh dashboard troubleshooting (Windows firewall fix)
- [[GNS3 VM IP Instability]] — GNS3 VM IP swapping fix
- [[Wazuh VM Static IP]] — Wazuh VM static IP fix