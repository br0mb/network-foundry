# Samba AD DC — Administrator Command Reference

> **Purpose:** Quick-reference cheat sheet for managing users, groups, passwords, DNS, and services on a Samba AD Domain Controller. Each section includes the equivalent Windows Server / PowerShell command for comparison.

---

## User Management

### Create a user
```bash
sudo samba-tool user create <username> <password> --given-name=<first> --surname=<last>
```
**Windows equivalent:** `New-ADUser -Name "John Smith" -SamAccountName "jsmith"`

### List all users
```bash
sudo samba-tool user list
```

### Delete a user
```bash
sudo samba-tool user delete <username>
```

### Disable / Enable a user
```bash
sudo samba-tool user disable <username>
sudo samba-tool user enable <username>
```

### Check user status (look for userAccountControl: 512=enabled, 514=disabled)
```bash
sudo samba-tool user show <username>
```

### Reset password
```bash
sudo samba-tool user setpassword <username> --newpassword=<password>
```

---

## Group Management

### Create a group
```bash
sudo samba-tool group add <groupname> --description="Description"
```

### List all groups
```bash
sudo samba-tool group list
```

### List group members
```bash
sudo samba-tool group listmembers <groupname>
```

### Add users to a group
```bash
sudo samba-tool group addmembers <groupname> <user1> <user2>
```

### Remove users from a group
```bash
sudo samba-tool group removemembers <groupname> <user1>
```

---

## DNS Management

### List all DNS records in a zone
```bash
sudo samba-tool dns query localhost foundry.local @ ALL -U Administrator
```

### Add an A record
```bash
sudo samba-tool dns add localhost foundry.local <hostname> A <ip> -U Administrator
```

### Add a CNAME record
```bash
sudo samba-tool dns add localhost foundry.local <alias> CNAME <target-fqdn> -U Administrator
```

### Delete a DNS record
```bash
sudo samba-tool dns delete localhost foundry.local <hostname> A <ip> -U Administrator
```

---

## Computer Management

### List all computer accounts
```bash
sudo samba-tool computer list
```

### Delete a computer account
```bash
sudo samba-tool computer delete <computername>
```

---

## Service Management

### Check Samba AD DC status
```bash
sudo systemctl status samba-ad-dc
```

### Restart Samba AD DC (fixes DNS binding issues after boot)
```bash
sudo systemctl restart samba-ad-dc
```

### Check which ports are listening
```bash
sudo ss -tlnp | grep :53    # DNS
sudo ss -tlnp | grep :88    # Kerberos
sudo ss -tlnp | grep :389   # LDAP
sudo ss -tlnp | grep :445   # SMB
```

---

## Domain Information

### Show domain info
```bash
sudo samba-tool domain info 127.0.0.1
```

### Show domain password policy
```bash
sudo samba-tool domain passwordsettings show
```

### Modify password policy
```bash
sudo samba-tool domain passwordsettings set --min-pwd-length=8
sudo samba-tool domain passwordsettings set --complexity=on
```

---

## Kerberos Testing

### Get a ticket for a user
```bash
kinit <username>@FOUNDRY.LOCAL
```

### View current tickets
```bash
klist
```

### Destroy tickets
```bash
kdestroy
```

---

## Key Differences: Samba AD vs Windows Server AD

### What's the Same
- Both implement full AD: LDAP, Kerberos, DNS, SMB, Global Catalog
- Same built-in groups, same authentication flow
- Windows clients can join either without knowing the difference
- Same DNS-integrated zones and SRV records

### What's Different
- **Config:** Samba uses a single text file (smb.conf). Windows uses registry, GPO, and AD itself.
- **GUI:** Samba is CLI-driven. Windows has ADUC, DNS Manager, GPMC. (RSAT from Windows can manage Samba AD.)
- **GPOs:** Samba can host GPOs but doesn't have a native editor. Manage from Windows with RSAT.
- **PowerShell:** PowerShell AD module works against Samba from a Windows machine. On the Linux DC, use samba-tool.

---

## Daily Operations — The 10 Commands You'll Actually Use

```bash
# 1. Create a user
sudo samba-tool user create jsmith Password123 --given-name=John --surname=Smith

# 2. Reset a password
sudo samba-tool user setpassword jsmith --newpassword=NewPass123

# 3. Disable a user
sudo samba-tool user disable jsmith

# 4. List all users
sudo samba-tool user list

# 5. Create a group
sudo samba-tool group add IT_Staff --description="IT Support Team"

# 6. Add user to group
sudo samba-tool group addmembers IT_Staff jsmith

# 7. List group members
sudo samba-tool group listmembers "Domain Admins"

# 8. Add a DNS record
sudo samba-tool dns add localhost foundry.local server1 A 10.0.24.20 -U Administrator

# 9. Check service is running
sudo systemctl status samba-ad-dc

# 10. Test authentication
kinit jsmith@FOUNDRY.LOCAL && klist
```