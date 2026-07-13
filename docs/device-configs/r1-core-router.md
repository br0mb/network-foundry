# R1 — Core Router Configuration

> **Device:** R1
> **Model:** Cisco 2650XM
> **IOS:** 12.4(15)T4
> **IP:** 10.0.24.1/21
> **Role:** Core routing, inter-VLAN routing, DHCP server, OSPF

---

## Running Configuration (Sanitized)

```
!
version 12.4
service timestamps debug datetime msec
service timestamps log datetime msec
no service password-encryption
!
hostname R1
!
boot-start-marker
boot-end-marker
!
no aaa new-model
!
resource policy
!
ip subnet-zero
ip cef
!
no ip dhcp use vrf connected
ip dhcp excluded-address 10.0.24.1 10.0.24.15
!
-- DHCP pool: VLAN 9 (Guests) --
ip dhcp pool VLAN9
   network 10.0.8.0 255.255.254.0
   default-router 10.0.8.1
   dns-server 10.0.24.1
   lease 7
!
-- DHCP pool: VLAN 10 (IT Staff) --
ip dhcp pool VLAN10
   network 10.0.10.0 255.255.255.0
   default-router 10.0.10.1
   dns-server 10.0.24.1
   lease 7
!
-- DHCP pool: VLAN 11 (Engineering) --
ip dhcp pool VLAN11
   network 10.0.11.0 255.255.255.0
   default-router 10.0.11.1
   dns-server 10.0.24.1
   lease 7
!
-- DHCP pool: VLAN 12 (Finance) --
ip dhcp pool VLAN12
   network 10.0.12.0 255.255.255.0
   default-router 10.0.12.1
   dns-server 10.0.24.1
   lease 7
!
-- DHCP pool: VLAN 13 (HR) --
ip dhcp pool VLAN13
   network 10.0.13.0 255.255.255.0
   default-router 10.0.13.1
   dns-server 10.0.24.1
   lease 7
!
-- DHCP pool: VLAN 14 (Printers) --
ip dhcp pool VLAN14
   network 10.0.14.0 255.255.255.0
   default-router 10.0.14.1
   dns-server 10.0.24.1
   lease 7
!
-- DHCP pool: VLAN 15 (Management) --
ip dhcp pool VLAN15
   network 10.0.15.0 255.255.255.0
   default-router 10.0.15.1
   dns-server 10.0.24.1
   lease 7
!
-- DHCP pool: VLAN 17 (DMZ) --
ip dhcp pool VLAN17
   network 10.0.16.0 255.255.252.0
   default-router 10.0.16.1
   dns-server 10.0.24.1
   lease 7
!
-- DHCP pool: VLAN 18 (Experimental) --
ip dhcp pool VLAN18
   network 10.0.20.0 255.255.254.0
   default-router 10.0.20.1
   dns-server 10.0.24.1
   lease 7
!
-- DHCP pool: VLAN 19 (IDS) --
ip dhcp pool VLAN19
   network 10.0.22.0 255.255.255.0
   default-router 10.0.22.1
   dns-server 10.0.24.1
   lease 7
!
-- DHCP pool: VLAN 24 (Infrastructure) --
ip dhcp pool VLAN24
   network 10.0.24.0 255.255.248.0
   default-router 10.0.24.1
   dns-server 10.0.24.1
   lease 7
!
!
-- SNMP Configuration --
snmp-server community public RO
snmp-server contact "Admin - admin@lab.local"
snmp-server location "Network Foundry Lab - Home Lab Rack"
snmp-server enable traps
snmp-server host 10.0.24.10 version 2c public
!
-- DNS Forwarding --
ip name-server 10.0.24.10
!
-- SSH Configuration --
ip ssh time-out 60
ip ssh authentication-retries 3
ip ssh version 2
!
username admin privilege 15 secret [REDACTED]
!
interface FastEthernet0/0
 description -- Trunk to SW-1 --
 no ip address
 speed 100
 full-duplex
!
interface FastEthernet0/0.9
 description -- Guest VLAN --
 encapsulation dot1Q 9
 ip address 10.0.8.1 255.255.254.0
!
interface FastEthernet0/0.10
 description -- IT Staff VLAN --
 encapsulation dot1Q 10
 ip address 10.0.10.1 255.255.255.0
!
interface FastEthernet0/0.11
 description -- Engineering VLAN --
 encapsulation dot1Q 11
 ip address 10.0.11.1 255.255.255.0
!
interface FastEthernet0/0.12
 description -- Finance VLAN --
 encapsulation dot1Q 12
 ip address 10.0.12.1 255.255.255.0
!
interface FastEthernet0/0.13
 description -- HR VLAN --
 encapsulation dot1Q 13
 ip address 10.0.13.1 255.255.255.0
!
interface FastEthernet0/0.14
 description -- Printers VLAN --
 encapsulation dot1Q 14
 ip address 10.0.14.1 255.255.255.0
!
interface FastEthernet0/0.15
 description -- Management VLAN --
 encapsulation dot1Q 15
 ip address 10.0.15.1 255.255.255.0
!
interface FastEthernet0/0.17
 description -- DMZ VLAN --
 encapsulation dot1Q 17
 ip address 10.0.16.1 255.255.252.0
!
interface FastEthernet0/0.18
 description -- Experimental VLAN --
 encapsulation dot1Q 18
 ip address 10.0.20.1 255.255.254.0
!
interface FastEthernet0/0.19
 description -- IDS VLAN --
 encapsulation dot1Q 19
 ip address 10.0.22.1 255.255.255.0
!
interface FastEthernet0/0.24
 description -- Infrastructure VLAN --
 encapsulation dot1Q 24
 ip address 10.0.24.1 255.255.248.0
!
interface Serial0/0
 description -- Link to R2-ISP (OSPF demo stub) --
 ip address 10.0.0.249 255.255.255.252
 clock rate 64000
!
-- OSPF Configuration --
router ospf 1
 log-adjacency-changes
 network 10.0.0.248 0.0.0.3 area 0
 network 10.0.24.0 0.0.7.255 area 0
 default-information originate
!
ip classless
!
line con 0
 exec-timeout 0 0
 password [REDACTED]
 login local
line aux 0
line vty 0 4
 password [REDACTED]
 login local
 transport input ssh
!
end
```

---

## Key Configuration Notes

- **Inter-VLAN Routing:** R1 uses 802.1Q sub-interfaces on FastEthernet0/0 for inter-VLAN routing. Each VLAN has its own sub-interface with the appropriate encapsulation and IP address.
- **DHCP Server:** R1 serves DHCP for all VLANs (9-24). DHCP exclusions are configured for `.1` (gateway) and `.13-.15` (static VMs).
- **DNS Forwarding:** R1 forwards DNS queries to the Samba DC at 10.0.24.10. R1 does NOT run `ip dns server` (caused CPU hog).
- **OSPF:** Single area 0, with a serial link to R2-ISP (demo stub). R1 originates a default route.
- **SSH:** Version 2 with legacy crypto support (diffie-hellman-group1-sha1). Key-based auth with password fallback.
- **SNMP:** v2c with community string `public` (read-only). Traps sent to Zabbix server at 10.0.24.10.

---

## Related Files

- [[Network Reference]] — Full network documentation
- [[SW-1 Core Switch]] — Core switch configuration