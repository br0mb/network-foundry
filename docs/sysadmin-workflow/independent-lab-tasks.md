# Independent Lab — Progressive Difficulty Tasks

> **Purpose:** Prove that theoretical knowledge can be applied independently using documentation, without a guide walking through each step. Tasks progress from easy to hard, mirroring the skill development curve of a junior sysadmin.

## Task Summary

| Task | Difficulty | Skill Area | Description |
|------|-----------|------------|-------------|
| 1 | Easy | Operations | Reboot client, verify all services survive |
| 2 | Easy | Operations | Reboot server, verify all services survive |
| 3 | Easy-Medium | AD Management | Create domain user and group, verify from client |
| 4 | Medium | DNS | Add A records and CNAMEs, test resolution from both sides |
| 5 | Medium | File Services | Create Samba share with group-based permissions, test access |
| 6 | Medium | VPN | Start WireGuard, verify handshake, ping through tunnel, SSH via tunnel |
| 7 | Medium | AD Management | Disable user, verify auth fails, re-enable, reset password, verify auth works |
| 8 | Hard | DHCP | Install ISC DHCP server, configure scope, set up router relay, test with live client |
| 9 | Hard | Print Server | Install CUPS, configure virtual PDF printer, test from server and client |
| 10 | Hard | Operations | Full reboot of all systems, verify everything survives and comes back clean |

## Difficulty Progression

### Easy (Tasks 1-2)
Reboot verification — the first thing a sysadmin checks after making changes. If it doesn't survive a reboot, the work isn't done. Tasks test whether configurations are persistent (netplan, iptables-persistent, systemd services enabled on boot).

### Easy-Medium (Task 3)
User and group creation — the most common sysadmin task. Tests AD management skills and cross-system verification (create on DC, verify from client).

### Medium (Tasks 4-7)
Infrastructure operations — DNS record management, file share configuration, VPN operation, and account lifecycle management. These tasks require understanding multiple systems working together (DNS resolution, Samba permissions, Kerberos authentication).

### Hard (Tasks 8-10)
Infrastructure builds — DHCP server with router relay, CUPS print server with virtual printer, and full reboot survival test. These tasks require integrating multiple systems (DHCP server + router relay + client lease), configuring services from scratch (CUPS installation, network binding, PDF printer setup), and verifying everything is persistent.

## Rules

1. Use the reference documentation as your runbook
2. If the reference doesn't cover it, use `--help`, `man` pages, or search
3. Don't ask for help until you've tried the reference AND searched yourself
4. Document what breaks and how you fixed it
5. If you complete tasks 1-7, you've proven you can handle routine sysadmin work independently
6. If you complete tasks 8-10, you've proven you can build infrastructure independently

## Key Lessons Documented

- Domain users need `FOUNDRY\\` prefix for local lookup, not bare username
- AD groups exist in the directory, not in `/etc/group` — `chown` can't use them directly
- Filesystem permissions and Samba permissions are two separate layers
- WireGuard fails silently on key mismatches — no error messages
- CUPS and Samba DNS bind to localhost by default — need config changes for network access
- systemd-resolved needs both DNS server AND search domain configured
- DHCP server needs subnet declaration for its own interface, even if not serving it
- iptables rules need iptables-persistent to survive reboots
- Boot order matters: network gear first, then VMs (services bind to interfaces that must be up)
- Route metrics determine which default gateway wins when multiple exist

---

*This lab was designed to test independent execution capability. The engineer worked through tasks using only reference documentation, troubleshooting when the documentation didn't predict the issue, and asking targeted questions only after attempting self-resolution.*