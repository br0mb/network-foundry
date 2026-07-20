# Build Report: Linux Client AD Domain Join

> **Date:** July 18, 2026
> **Infrastructure:** Ubuntu Desktop VM joined to Samba Active Directory domain

## What Was Built

An Ubuntu Desktop VM was joined to the Active Directory domain, enabling domain users to log in with their AD credentials. The join uses realmd for orchestration, sssd for ongoing authentication, and Kerberos for ticket-based identity verification.

## Architecture

```
Ubuntu Client (10.0.24.17)
   |
   | realmd discovers domain via DNS SRV records
   | adcli creates computer account in AD
   | sssd handles ongoing authentication
   | PAM/NSS connect sssd to Linux login system
   | oddjob-mkhomedir creates home directories on first login
   | krb5-user manages Kerberos tickets
   v
Domain Controller (Samba AD DC)
   - LDAP (389/636): directory queries
   - Kerberos (88): authentication
   - DNS (53): service discovery
   - SMB (445): Netlogon
```

## Configuration Steps

### 1. Network Prerequisites
- Client on lab network with correct IP, gateway, and DNS
- DNS pointing at domain controller (not router) for SRV record resolution
- Search domain configured for the AD domain
- Internet access through NAT gateway for package installation

### 2. Package Installation
Installed: realmd, sssd, sssd-tools, libnss-sss, libpam-sss, adcli, samba-common-bin, oddjob, oddjob-mkhomedir, packagekit, krb5-user

Kerberos default realm set to the AD domain name (uppercase).

### 3. Domain Discovery
`realm discover` confirmed the domain was found via DNS SRV records, identified as Active Directory with Kerberos, and all required packages were present.

### 4. Domain Join
`realm join` authenticated with domain admin credentials, created a computer account in AD, generated a Kerberos keytab, and configured sssd.

### 5. Home Directory Creation
Enabled `pam-auth-update --enable mkhomedir` and restarted oddjobd so domain users get home directories on first login.

## Troubleshooting Issues

### Issue 1: DNS SRV Records Refused
**Cause:** Client was using the router as DNS, which doesn't serve SRV records properly. Changed DNS to the domain controller directly.
**Fix:** Updated DNS in network settings, added search domain via `resolvectl domain`, flushed DNS cache.

### Issue 2: No Internet for Package Installation
**Cause:** Lab network has no internet. The client needed packages but couldn't reach repositories.
**Fix:** Configured the domain controller as a NAT gateway (see NAT Gateway build report).

### Issue 3: Join Failed — "Preauthentication Failed"
**Cause:** Password confusion between local Ubuntu account and AD Administrator account (different passwords with similar patterns).
**Fix:** Used the correct AD Administrator password. Diagnosed via `journalctl REALMD_OPERATION=<id>`.

### Issue 4: Home Directory Not Created on Login
**Cause:** oddjob-mkhomedir was not enabled in PAM.
**Fix:** `sudo pam-auth-update --enable mkhomedir` + `sudo systemctl restart oddjobd`

## Verification

- `realm list` — domain joined ✅
- `id FOUNDRY\\user` — OS sees domain user ✅
- `kinit user@FOUNDRY.LOCAL` — Kerberos TGT obtained ✅
- `klist` — ticket valid for 10 hours, renewable for 24 ✅
- `su - FOUNDRY\\user` — login successful, home directory created ✅

## Enterprise Relevance

| Concept | Enterprise Equivalent |
|---------|----------------------|
| Linux domain join | Linux servers/workstations in corporate AD environments |
| Kerberos authentication | Standard AD authentication mechanism |
| sssd configuration | Centralized identity management for Linux |
| DNS service discovery | AD auto-discovery via SRV records |
| Home directory auto-creation | Enterprise user onboarding |
| systemd-resolved troubleshooting | Linux DNS issues in mixed environments |