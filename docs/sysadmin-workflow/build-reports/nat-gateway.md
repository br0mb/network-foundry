# Build Report: NAT Gateway for Internet Access

> **Date:** July 17, 2026
> **Infrastructure:** Domain controller configured as NAT gateway for isolated lab network

## What Was Built

The domain controller was configured as a NAT gateway so that lab clients on an isolated network (no direct internet access) can reach the internet through the server's second network interface. This mirrors the corporate pattern where internal networks have no direct internet access and a gateway handles the translation.

## Architecture

```
Lab Client (10.0.24.x)                     Server (Domain Controller)
   |                                        ens33: 10.0.24.10 (lab, no internet)
   |  default gateway → 10.0.24.10    →    ens37: 192.168.x.x (home network, has internet)
   |                                        IP forwarding: enabled
   v                                        NAT/MASQUERADE: lab → internet
Internet (via server NAT → home router → ISP)
```

## Packet Flow

1. Client sends packet to 8.8.8.8 (source: 10.0.24.x, dest: 8.8.8.8)
2. Packet arrives at server on lab interface
3. Kernel forwards packet (IP forwarding enabled) to internet interface
4. MASQUERADE rewrites source IP from 10.0.24.x to server's internet IP
5. Packet goes out to internet through home router
6. Response returns, NAT reverses translation, packet forwarded back to client
7. Client receives response — entire NAT process transparent

## Configuration

Three iptables rules:
- MASQUERADE: Source NAT for lab traffic going out the internet interface
- FORWARD accept (outbound): Allow lab traffic to reach internet
- FORWARD accept (inbound): Allow return traffic from internet back to lab

Plus IP forwarding enabled at the kernel level (`net.ipv4.ip_forward = 1`).

Persistence: Rules saved via `iptables-persistent` to survive reboots.

## Why the Client Doesn't Need a Second Adapter

The client only has one network adapter on the lab network. It doesn't need direct internet connectivity — it sends traffic to its default gateway (the server), and the gateway handles internet access on its behalf. This is how every corporate network works: clients are on internal subnets with no direct internet, and a router or firewall handles NAT translation.

## Enterprise Relevance

| Concept | Enterprise Equivalent |
|---------|----------------------|
| NAT gateway | Corporate firewall/router doing NAT for internal networks |
| IP forwarding | Any router or firewall forwarding between interfaces |
| MASQUERADE | Source NAT for private-to-public traffic |
| Client gateway configuration | Clients using corporate gateway for internet |
| Persistence (iptables-persistent) | Production firewall rule management |