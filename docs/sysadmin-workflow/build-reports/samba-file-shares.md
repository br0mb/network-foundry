# Build Report: Samba File Shares with Group-Based Permissions

> **Date:** July 19-20, 2026
> **Infrastructure:** Department-based file shares and personal home drives with AD group access control

## What Was Built

Samba file shares on the domain controller with Active Directory group-based access control. Department shares restrict access to members of specific AD groups. Personal home drives restrict access to individual users. Cross-department access is denied.

## Share Configuration

### Department Shares
Each department has a shared folder accessible only by members of that department's AD group:

```ini
[Department_Name]
   path = /srv/shared/Department_Name
   valid users = @"AD_Group_Name"
   read only = no
   browseable = yes
   create mask = 0660
   directory mask = 0770
```

### Personal Home Drives
Each user has a personal home drive accessible only by that user:

```ini
[home_username]
   path = /srv/home/username
   valid users = FOUNDRY\\username
   read only = no
   browseable = no
   create mask = 0600
   directory mask = 0700
```

## Access Control Model

Two separate layers of permission:

1. **Samba layer (valid users):** Controls which AD users and groups can access the share. This is the primary access control — Samba checks AD group membership before allowing connection.

2. **Filesystem layer (chmod):** Controls OS-level read/write/execute. The directory must be permissive enough for Samba to write files on behalf of authenticated users.

Key learning: AD groups exist in the directory database, not in `/etc/group`. The `chown` command can't use AD group names — it only sees local Linux groups. Samba handles AD group authorization through its own `valid users` directive, independent of filesystem ownership.

## Verification

- Department members can access their department share ✅
- Department members are denied access to other departments' shares ✅
- Users can access their own home drive ✅
- Users are denied access to other users' home drives ✅
- Files written through Samba appear on the server with correct AD UID ownership ✅

## Enterprise Relevance

| Concept | Enterprise Equivalent |
|---------|----------------------|
| Department shares | Corporate shared drives with group-based access |
| Home drives | Personal network storage for users |
| AD group permissions | Access control via directory service groups |
| Samba valid users | Share-level authorization |
| Filesystem permissions | OS-level access control |
| Cross-department denial | Security isolation between departments |