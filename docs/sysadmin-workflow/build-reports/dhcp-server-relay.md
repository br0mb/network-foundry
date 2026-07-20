# Build Report: DHCP Server with Router Relay

> **Date:** July 18-19, 2026
> **Infrastructure:** ISC DHCP server on domain controller, Cisco router as DHCP relay

## What Was Built

A central DHCP server (ISC DHCP) on the domain controller serving IP addresses to clients on a different VLAN. The Cisco router acts as a DHCP relay, forwarding client broadcasts to the central server. This is the enterprise pattern for centralized DHCP management.

## Architecture

```
VLAN 10 Client                      Cisco Router                  DHCP Server
(broadcasts DHCP)     →    Fa0/0.10 (10.0.10.1)     →    (10.0.24.10)
                      ip helper-address 10.0.24.10       ISC DHCP running
                                                         Scope: 10.0.10.100-200
                                                         Gateway: 10.0.10.1
                                                         DNS: 10.0.24.10
```

## Configuration Steps

### 1. Install and Configure ISC DHCP Server
- Install `isc-dhcp-server` package
- Configure interface in `/etc/default/isc-dhcp-server`
- Create DHCP scope in `/etc/dhcp/dhcpd.conf`:
  - Network: 10.0.10.0/24
  - Range: 10.0.10.100 - 10.0.10.200
  - Default gateway: 10.0.10.1 (router's VLAN 10 interface)
  - DNS: 10.0.24.10 (domain controller)
  - Domain name: foundry.local
  - Lease time: 8 hours

### 2. Add Empty Subnet for Server's Own Network
The DHCP server needs a subnet declaration for its own interface, even if it's not serving IPs there. Without this, the service refuses to start ("No subnet declaration for ens33").

### 3. Remove Router's Native DHCP Pool
The router was previously serving DHCP for all VLANs. The pool for VLAN 10 was removed to avoid conflicts with the new central server.

### 4. Configure DHCP Relay on the Router
Added `ip helper-address` to the router's VLAN 10 sub-interface. This tells the router to intercept DHCP broadcasts on VLAN 10 and forward them as unicasts to the DHCP server.

### 5. Add Static Route for Return Traffic
The DHCP server needed a route to reach VLAN 10's network. Without it, the DHCP OFFER was being sent through the internet interface instead of the lab interface, and the offer never reached the client.

Fix: Added a static route (`10.0.0.0/16 via router`) so all internal VLAN traffic goes through the router, not the internet gateway.

## Troubleshooting Issues

### Issue 1: "Not configured to listen on any interfaces"
**Cause:** DHCP server config only had a scope for VLAN 10, but the server's interface is on a different network.
**Fix:** Added an empty subnet declaration for the server's own network.

### Issue 2: DHCP DISCOVER received but client gets APIPA
**Cause:** The DHCP OFFER was being routed through the internet interface instead of the lab interface. The server's default route pointed to the home router, not the lab router.
**Fix:** Added a static route for all internal VLAN networks pointing to the lab router. The OFFER then went through the correct interface and reached the client.

## Verification

```
DHCPDISCOVER from client via 10.0.10.1     ← Router relayed the broadcast
DHCPOFFER on 10.0.10.100 to client          ← Server offered an IP
DHCPACK on 10.0.10.100 to client            ← Lease confirmed
```

Client received IP 10.0.10.100 with correct gateway, DNS, and domain name.

## Enterprise Relevance

| Concept | Enterprise Equivalent |
|---------|----------------------|
| Central DHCP server | Enterprise DHCP on a dedicated server or appliance |
| DHCP relay (ip helper) | Router relaying DHCP across VLANs |
| Scope configuration | DHCP pool with options (gateway, DNS, domain, lease time) |
| Route conflicts | Routing table troubleshooting in multi-interface servers |
| Service persistence | systemd service management and enablement |