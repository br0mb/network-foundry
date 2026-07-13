# SW-1 — Core Switch Configuration

> **Device:** SW-1
> **Model:** Cisco WS-C3750
> **IP:** 10.0.24.11/21
> **Role:** Core switch, VLAN trunking, Layer 2 access

---

## Running Configuration (Sanitized)

```
!
version 12.2
no service pad
service timestamps debug uptime
service timestamps log uptime
no service password-encryption
!
hostname SW-1
!
no aaa new-model
!
system mtu routing 1500
ip subnet-zero
!
no ip domain-lookup
!
-- VLAN Database --
vlan 9
 name GUEST
vlan 10
 name IT_STAFF
vlan 11
 name ENGINEERING
vlan 12
 name FINANCE
vlan 13
 name HR
vlan 14
 name PRINTERS
vlan 15
 name MANAGEMENT
vlan 17
 name DMZ
vlan 18
 name EXPERIMENTAL
vlan 19
 name IDS
vlan 24
 name INFRASTRUCTURE
!
-- SNMP Configuration --
snmp-server community public RO
snmp-server contact "Admin - admin@lab.local"
snmp-server location "Network Foundry Lab - Core Switch"
snmp-server enable traps
snmp-server host 10.0.24.10 version 2c public
!
-- SSH Configuration --
ip ssh time-out 60
ip ssh authentication-retries 3
!
username admin privilege 15 secret [REDACTED]
!
-- Spanning Tree Configuration --
spanning-tree mode rapid-pvst
spanning-tree extend system-id
spanning-tree vlan 1-9,10-24 priority 24576
!
-- Trunk Port (to R1) --
interface GigabitEthernet0/1
 description -- Trunk to R1 --
 switchport trunk encapsulation dot1q
 switchport mode trunk
!
-- Access Ports (VLAN 24 - Infrastructure) --
interface FastEthernet0/1
 description -- lab-srv1 (Samba AD DC) --
 switchport access vlan 24
 switchport mode access
 spanning-tree portfast
!
interface FastEthernet0/2
 description -- Wazuh Manager VM --
 switchport access vlan 24
 switchport mode access
 spanning-tree portfast
!
interface FastEthernet0/3
 description -- GNS3 VM --
 switchport access vlan 24
 switchport mode access
 spanning-tree portfast
!
interface FastEthernet0/4
 description -- Spare --
 switchport access vlan 24
 switchport mode access
 spanning-tree portfast
!
interface FastEthernet0/5
 description -- Spare --
 switchport access vlan 24
 switchport mode access
 spanning-tree portfast
!
interface FastEthernet0/6
 description -- Spare --
 switchport access vlan 24
 switchport mode access
 spanning-tree portfast
!
interface FastEthernet0/7
 description -- Spare --
 switchport access vlan 24
 switchport mode access
 spanning-tree portfast
!
interface FastEthernet0/8
 description -- Spare --
 switchport access vlan 24
 switchport mode access
 spanning-tree portfast
!
-- Access Ports (VLAN 10 - IT Staff) --
interface FastEthernet0/9
 description -- IT Staff Port --
 switchport access vlan 10
 switchport mode access
 spanning-tree portfast
!
interface FastEthernet0/10
 description -- IT Staff Port --
 switchport access vlan 10
 switchport mode access
 spanning-tree portfast
!
-- Access Ports (VLAN 11 - Engineering) --
interface FastEthernet0/11
 description -- Engineering Port --
 switchport access vlan 11
 switchport mode access
 spanning-tree portfast
!
interface FastEthernet0/12
 description -- Engineering Port --
 switchport access vlan 11
 switchport mode access
 spanning-tree portfast
!
-- Access Ports (VLAN 15 - Management) --
interface FastEthernet0/23
 description -- Management Port --
 switchport access vlan 15
 switchport mode access
 spanning-tree portfast
!
interface FastEthernet0/24
 description -- Management Port --
 switchport access vlan 15
 switchport mode access
 spanning-tree portfast
!
-- Management VLAN Interface --
interface Vlan24
 description -- Management Interface --
 ip address 10.0.24.11 255.255.248.0
!
ip default-gateway 10.0.24.1
!
line con 0
 exec-timeout 0 0
 password [REDACTED]
 login local
line vty 0 4
 password [REDACTED]
 login local
 transport input ssh
line vty 5 15
 login local
 transport input ssh
!
end
```

---

## Key Configuration Notes

- **VLAN Trunking:** GigabitEthernet0/1 is the trunk port to R1, carrying all VLANs using 802.1Q encapsulation.
- **Access Ports:** FastEthernet ports are assigned to VLANs based on function (infrastructure, IT staff, engineering, management).
- **Spanning Tree:** Rapid PVST+ is used. SW-1 is configured as root bridge (priority 24576) for all VLANs.
- **PortFast:** Enabled on all access ports for fast convergence on end-device connections.
- **Management:** The switch is managed via VLAN 24 interface (10.0.24.11) with default gateway 10.0.24.1 (R1).
- **SNMP:** v2c with community string `public` (read-only). Traps sent to Zabbix server at 10.0.24.10.
- **SSH:** Enabled with local authentication. Console and VTY lines use local user database.

---

## Related Files

- [[Network Reference]] — Full network documentation
- [[R1 Core Router]] — Core router configuration