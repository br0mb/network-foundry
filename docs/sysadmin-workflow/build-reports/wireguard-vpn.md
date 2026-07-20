# Build Report: WireGuard Remote Access VPN

> **Date:** July 17, 2026
> **Infrastructure:** WireGuard VPN tunnel between domain controller (server) and workstation (client)

## What Was Built

A WireGuard remote access VPN that tunnels an external client into the lab network. The server listens on UDP 51820 on its internet-facing interface. The client connects with key-based authentication and traffic is routed into the internal network through a tunnel interface (wg0) with NAT/MASQUERADE.

## Architecture

```
Client (Workstation)                        Server (Domain Controller)
   Internet IP  ----VPN tunnel (UDP 51820)----  Internet IP
        |                                              |
   Tunnel: 10.0.254.2                          Tunnel: 10.0.254.1
                                                      |
                                              Internal IP (lab network)
                                                      |
                                              Router, Switch, SIEM, etc.
```

## Key Configuration Decisions

- **Split tunneling:** Only lab network traffic goes through the VPN (AllowedIPs). Internet traffic goes direct. This prevents unnecessary bandwidth usage and latency for non-lab traffic.

- **MASQUERADE instead of return routing:** NAT on the server translates tunnel traffic to the server's lab IP. This avoids needing static routes on the router for the tunnel subnet. Simpler for remote access VPNs.

- **Key-based authentication:** WireGuard uses public/private key pairs — no passwords, no certificates, no TLS handshake. The private key never leaves the machine. More secure and simpler than certificate-based VPNs.

- **UFW firewall:** VPN port opened on internet interface, all traffic allowed from tunnel interface (peers are already authenticated by keys).

## Troubleshooting Issues Encountered

### Issue 1: Default Route Conflict
**Problem:** Server had two default routes — one via the lab router (no internet) and one via the home network (has internet). The lab router route had no metric (0, highest priority), so all internet traffic died.
**Fix:** Added metric 2000 to the lab router route in netplan. The home network route (metric 1024) now wins for internet traffic.

### Issue 2: DHCP IP Instability
**Problem:** Server's internet-facing IP changed on every reboot because DHCP assigned different addresses.
**Fix:** Added a DHCP reservation on the home router for the server's MAC address, reserving a static IP.

### Issue 3: Key Swap During Initial Configuration
**Problem:** Client config had the server's private key instead of the client's private key. WireGuard silently rejected the peer — no error message, just no handshake.
**Fix:** Generated separate client key pair and placed the correct keys in each config. Lesson: WireGuard's silent failure makes key mismatches hard to diagnose — `wg show` with no peer section means the peer was rejected.

### Issue 4: SSH to Server Failed Through Tunnel
**Problem:** Pings to other lab devices worked through the tunnel, but SSH to the server itself timed out.
**Fix:** UFW only had rules for the internet and lab interfaces. Added `ufw allow in on wg0` to allow traffic from the tunnel interface. Pings to other devices worked because they're forwarded traffic (FORWARD chain); SSH to the server is local traffic (INPUT chain). Different firewall paths.

### Issue 5: WSL Interface Naming
**Problem:** Attempted to add a route specifying `eth0` as the lab network interface, but `eth0` in WSL is the Hyper-V virtual network, not the lab network.
**Fix:** The SSH issue was actually caused by the missing UFW rule (Issue 4), not a routing problem. The route attempt was unnecessary.

## Verification Results

All lab devices reachable through the tunnel:
- Server tunnel IP: ✅
- Core router: ✅
- SIEM: ✅
- Network simulator: ✅
- Core switch: ✅
- SSH to server through tunnel: ✅

## Enterprise Relevance

| Concept | Enterprise Equivalent |
|---------|----------------------|
| Remote access VPN | VPN for remote workers |
| Key-based authentication | Certificate/key-based VPN security |
| Split tunneling | Corporate VPN configuration |
| NAT/MASQUERADE | Firewall/gateway NAT |
| Firewall rules for VPN | Security policy for remote access |
| Silent failure debugging | Security-focused system troubleshooting |