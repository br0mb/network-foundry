# Sysadmin Readiness Assessment — 130 Questions

> **Purpose:** Self-assessment covering the knowledge a hiring manager expects an entry-level sysadmin to know cold. Questions span subnetting, networking, Active Directory, Linux administration, VPN fundamentals, and troubleshooting scenarios.
> **Instructions:** Answer each question without looking anything up. Check your answers afterward. Questions you can't answer are your study targets.

---

## Section 1: Subnetting (50 Questions)

### CIDR to Subnet Mask (10 questions)
What is the subnet mask for /24, /25, /26, /27, /28, /29, /30, /22, /23, /20?

### Hosts Per Subnet (10 questions)
How many usable hosts in /24, /25, /26, /28, /30, /22, /23, /20, /27, /21?

### Network / First Usable / Last Usable / Broadcast (10 questions)
Given an IP and CIDR, identify the network address, first usable host, last usable host, and broadcast address for:
192.168.1.130/26, 10.0.10.50/24, 172.16.5.100/22, 10.0.0.5/30, 192.168.50.200/27, 10.0.24.10/21, 172.16.1.1/28, 192.168.10.75/25, 10.0.0.129/26, 192.168.68.14/22

### Subnet Design (10 questions)
Divide networks into subnets, calculate masks for host/subnet requirements, design VLSM schemes.

### Subnet Boundaries (10 questions)
Determine whether two IPs with the same CIDR are in the same subnet or different subnets.

## Section 2: Networking Fundamentals (30 Questions)

### DHCP (5 questions)
DORA process, DHCP relay, IP helper configuration, DHCP options, lease time

### DNS (6 questions)
Forward vs reverse lookup, A vs CNAME, recursive vs iterative, resolution process, DNS forwarding, secondary DNS behavior

### VLANs and Trunking (7 questions)
VLAN purpose, 802.1Q, access vs trunk ports, native VLAN, management VLAN isolation, inter-VLAN routing methods, troubleshooting cross-VLAN connectivity

### Routing (7 questions)
Static vs dynamic routes, OSPF, default routes, administrative distance, longest prefix match, NAT

### ARP and MAC (5 questions)
ARP function, MAC vs IP, same-subnet unreachable diagnosis, ARP at router boundaries, broadcast vs collision domains

## Section 3: Active Directory (15 Questions)

AD purpose, domain controllers, authentication vs authorization, Kerberos ticket exchange, domain vs local users, OUs, security vs distribution groups, Group Policy, login troubleshooting, LDAP, LDAPS, trust relationships, Global Catalog, password change propagation, domain/tree/forest hierarchy

## Section 4: Linux System Administration (15 Questions)

ip addr, systemctl status/start/stop/restart, journalctl, df, ss/netstat, useradd, usermod, chmod (755/644), ip route, resolv.conf, netplan, UFW, ip link, apt install

## Section 5: VPN Fundamentals (10 Questions)

VPN purpose, site-to-site vs remote access, split vs full tunnel, AllowedIPs, private vs public keys, NAT traversal/PersistentKeepalive, WireGuard vs OpenVPN, IPsec phases, tunnel interfaces, WireGuard silent failure

## Section 6: Troubleshooting Scenarios (10 Questions)

1. User on VLAN 10 can't reach server on VLAN 24 — first three checks
2. VPN won't connect — first three checks
3. Can ping server but can't SSH — first three checks
4. IP works but DNS doesn't — likely problem and confirmation
5. DHCP works on same VLAN but not cross-VLAN — what's missing
6. Account keeps getting locked out — three possible causes
7. WireGuard tunnel up but no traffic — three possible causes
8. Domain client can ping DC by IP but not by hostname — likely issue
9. Lost SSH after network change, have physical access — recovery
10. User getting 169.254.x.x — what it means and two causes

---

*Assessment covers fundamentals that a hiring manager expects an entry-level sysadmin or NOC technician to know cold. If you can answer 80% or more without looking anything up, you're prepared for interviews.*