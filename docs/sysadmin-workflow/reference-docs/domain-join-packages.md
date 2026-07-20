# Domain Join Package Reference — What Each Package Does

> **Purpose:** Reference for the packages required to join a Linux machine to an Active Directory domain

---

## The Packages

| Package | Role |
|---------|------|
| realmd | Orchestrator — discovers domain, coordinates the join |
| sssd | Background daemon — handles ongoing authentication |
| sssd-tools | CLI utilities for managing sssd |
| libnss-sss | Makes domain users visible to the OS (Name Service Switch) |
| libpam-sss | Routes login authentication through sssd to AD (PAM) |
| adcli | Performs the actual domain registration at the protocol level |
| samba-common-bin | Provides `net` and other Samba client tools |
| oddjob | Framework for running privileged tasks on behalf of users |
| oddjob-mkhomedir | Auto-creates home directories for domain users on first login |
| packagekit | Handles automatic dependency installation if needed |
| krb5-user | Kerberos client — handles ticket lifecycle (kinit, klist, kdestroy) |

## How They Work Together

When `realm join foundry.local` runs:

1. realmd discovers the domain via DNS (SRV records)
2. realmd calls adcli to create a computer account in AD
3. adcli authenticates with domain admin credentials
4. adcli creates the computer object and generates a keytab
5. realmd configures sssd with the domain info
6. sssd starts communicating with the DC (LDAP, Kerberos)
7. libnss-sss makes domain users visible to the OS
8. libpam-sss routes login authentication through sssd to AD
9. oddjob-mkhomedir creates home directories on first login
10. krb5-user handles Kerberos ticket lifecycle

After the join, when a domain user logs in:

1. User types username and password at login screen
2. PAM (via libpam-sss) sends credentials to sssd
3. sssd sends authentication request to the domain controller
4. DC validates against AD database
5. DC issues a Kerberos ticket (via krb5-user)
6. sssd caches the user info (via libnss-sss)
7. oddjob-mkhomedir creates home directory if needed
8. User is logged in with their AD credentials

---

## Verification Commands

```bash
# Check which domains are joined
realm list

# Check if a domain user is recognized
id FOUNDRY\\<username>

# Get a Kerberos ticket
kinit <username>@FOUNDRY.LOCAL

# Verify the ticket
klist

# Check sssd status
systemctl status sssd

# Check sssd logs if something fails
journalctl -u sssd -n 50
```