# Daily Ticket System — Automated Task Generation

## Overview

The daily ticket system generates a structured sysadmin practice ticket every day via cron. Each ticket contains a morning checkup, an assigned task, and an end-of-day summary — mirroring the workflow of a real IT support ticketing system.

## How It Works

### Cron Schedule

A cron job runs at 2:00 PM daily, 30 minutes before the engineer's "shift" starts at 2:30 PM. The job executes a Python script that:

1. Determines the current day of the week and which week of the 4-week rotation
2. Looks up the assigned task for that day from the rotation schedule
3. Generates a markdown ticket file with the morning checkup, task details, and summary template
4. Saves the ticket to the tickets directory

### Ticket Structure

Each ticket file contains:

```
# Daily Ticket — [Day], Week [N]
> Date, assignee, priority, category, description, references

## Morning Checkup
  ### Server Health — service status, port binding, routes, internet
  ### Network Health — ping all lab devices
  ### Client Health — gateway, DNS, internet, domain users
  ### Security Check — SSH logs, firewall, DHCP leases
  ### Log Review — system errors, service warnings
  ### Morning Summary — checklist with ✅/❌

## Ticket: [ID] — [Task Area]
  Description and checkboxes for the assigned task
  Reference pointers to documentation files

## End of Day
  Status, time spent, issues, what I learned
```

### 4-Week Rotation

The rotation cycles through all major sysadmin skill areas:

**Week 1 — Fundamentals**
- Monday: Documentation & Maintenance
- Tuesday: User Management (create users, groups, verify from client)
- Wednesday: DNS Management (A records, CNAMEs, resolution testing)
- Thursday: File Services (department shares, home drives, permissions)
- Friday: Security Review (firewall audit, SSH logs, user audit, password policy)
- Saturday: Monitoring (Zabbix, Wazuh, system health)
- Sunday: Lab Maintenance (cleanup, disk space, review)

**Week 2 — Infrastructure Expansion**
- Monday: Documentation
- Tuesday: DHCP Management (new scope, relay, testing)
- Wednesday: Print Server (second printer, cleanup, queue management)
- Thursday: Backup Practice (Samba AD, R1 config, CUPS config, restore testing)
- Friday: VPN Management (WireGuard operation, key rotation, second client)
- Saturday: Monitoring
- Sunday: Lab Maintenance

**Week 3 — Advanced Operations**
- Monday: Documentation
- Tuesday: Server Migration (plan and execute DHCP service migration)
- Wednesday: Patch Management (security updates, unattended-upgrades, package conflict resolution)
- Thursday: Certificate Authority (OpenSSL CA, sign certificates, install in CUPS)
- Friday: Security Hardening (SSH hardening, fail2ban, port changes)
- Saturday: Monitoring
- Sunday: Lab Maintenance

**Week 4 — Mastery & Review**
- Monday: Documentation (full review, portfolio update)
- Tuesday: Disaster Recovery (simulate failures, diagnose, recover, document)
- Wednesday: Automation (bash script for morning checkup, cron scheduling)
- Thursday: Network Troubleshooting (simulate issues, diagnose from client side, fix)
- Friday: Full Audit (users, groups, firewall, services, file shares, DNS)
- Saturday: Monthly Monitoring Review
- Sunday: Monthly Review (skills assessment, resume update, plan next month)

### Task-to-Job Mapping

Every task in the rotation maps to responsibilities found in real Systems Administrator and MSP IT Engineer job descriptions:

| Rotation Task | Job Description Match |
|--------------|----------------------|
| Morning checkup | "Ensure stability and reliability of assigned client environments" |
| User management | "Manage Windows Server environments (AD, identity issues)" |
| DNS management | "Manage DNS" |
| File services | "File services with permissions" |
| Security review | "Implement secure configurations" |
| DHCP management | "VLAN and subnet design within defined standards" |
| Print server | "End-user support" |
| Backup practice | "Infrastructure upgrades and migrations" |
| VPN management | "Firewall and VPN configuration and administration" |
| Patch management | "Patch management" |
| Server migration | "Lead infrastructure upgrades and migrations" |
| Disaster recovery | "Proven troubleshooting methodology" |
| Automation | "Reduce repeat issues through documentation and training" |
| Full audit | "Accountability, documentation, and disciplined execution" |
| Documentation | "Document your work so others can execute it without you" |

## Design Principles

1. **Documentation-first:** Tasks reference existing documentation. When the documentation doesn't cover something, the engineer uses `--help`, `man` pages, or search — the same escalation path used at a real job.

2. **Progressive difficulty:** Week 1 covers fundamentals. Week 2 expands infrastructure. Week 3 introduces advanced operations. Week 4 tests mastery through disaster recovery, automation, and full audits.

3. **Repetition builds fluency:** The morning checkup is the same every day. After two weeks, the commands become muscle memory. After four weeks, checking service status and reading logs is automatic.

4. **Real failures, real troubleshooting:** Tasks are designed to produce real issues — service binding problems, DNS resolution failures, permission denied errors, route conflicts. The engineer troubleshoots these the same way they would in production.

5. **Documentation as output:** Every task completion includes documenting what was done, what broke, and what was learned. This builds the documentation discipline that employers value.

---

*The ticket generation script is included in the `scripts/` directory. It is a standalone Python script that generates daily tickets based on the 4-week rotation schedule.*