# WireGuard VPN Build Guide

> **Purpose:** Complete guide for building a WireGuard remote access VPN on a Linux server

---

## What WireGuard Is

WireGuard is a modern VPN protocol that uses public-key cryptography for authentication and creates a virtual network interface (wg0) that encrypts traffic at one end and decrypts at the other. It's simpler than OpenVPN (no certificates, no TLS) and faster than IPsec (kernel-level implementation).

## Core Concepts

### Key Pairs
Each side generates a key pair:
- **Private key:** Stays on the machine, never shared
- **Public key:** Shared with the peer for encryption/verification

### AllowedIPs
Does two things simultaneously:
- **Routing:** Tells the OS which destinations go through the tunnel
- **Access control:** On the server, defines which source IPs each peer can use

### Split Tunneling
Only specific traffic goes through the VPN. Everything else goes direct. Controlled by AllowedIPs.

### Silent Failure
WireGuard doesn't respond to unauthenticated traffic. If keys don't match, the handshake silently fails — no error messages. This is a security feature, not a bug.

---

## Server Configuration

### Install WireGuard
```bash
sudo apt install -y wireguard wireguard-tools
```

### Generate Server Keys
```bash
wg genkey | tee server_private.key | wg pubkey > server_public.key
```

### Generate Client Keys
```bash
wg genkey | tee client_private.key | wg pubkey > client_public.key
```

### Create Server Config (`/etc/wireguard/wg0.conf`)
```ini
[Interface]
PrivateKey = <server_private_key>
Address = 10.0.254.1/24
ListenPort = 51820

PostUp = iptables -A FORWARD -i wg0 -o <lan_interface> -j ACCEPT; iptables -A FORWARD -i <lan_interface> -o wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o <lan_interface> -j MASQUERADE
PostDown = iptables -D FORWARD -i wg0 -o <lan_interface> -j ACCEPT; iptables -D FORWARD -i <lan_interface> -o wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o <lan_interface> -j MASQUERADE

[Peer]
PublicKey = <client_public_key>
AllowedIPs = 10.0.254.2/32
```

### Enable IP Forwarding
```bash
sudo sysctl -w net.ipv4.ip_forward=1
echo "net.ipv4.ip_forward = 1" | sudo tee /etc/sysctl.d/99-wireguard.conf
```

### Open Firewall
```bash
sudo ufw allow in on <internet_interface> proto udp from any to any port 51820
sudo ufw allow in on wg0
```

### Start the Tunnel
```bash
sudo wg-quick up wg0
sudo wg show
```

---

## Client Configuration

### Create Client Config (`/etc/wireguard/wg0.conf`)
```ini
[Interface]
PrivateKey = <client_private_key>
Address = 10.0.254.2/24
DNS = <dns_server_ip>

[Peer]
PublicKey = <server_public_key>
Endpoint = <server_public_ip>:51820
AllowedIPs = <lan_network>/<cidr>, 10.0.254.0/24
PersistentKeepalive = 25
```

### Start the Client
```bash
sudo wg-quick up wg0
sudo wg show
```

Look for `latest handshake: X seconds ago` — if present, tunnel is connected.

---

## Verification

```bash
# Ping server's tunnel IP
ping -c 3 10.0.254.1

# Ping LAN devices through tunnel
ping -c 3 <lan_device_ip>

# SSH to server through tunnel
ssh <user>@10.0.254.1

# Verify traffic goes through tunnel
ip route get <lan_device_ip>
# Should show "dev wg0"
```

---

## Troubleshooting

### No handshake in wg show
- Check endpoint IP is reachable
- Check firewall allows UDP 51820
- Verify keys match (server has client's public, client has server's public)

### Handshake but no traffic
- Check IP forwarding is enabled
- Check iptables FORWARD rules
- Check UFW allows wg0

### SSH to server fails but pings to other devices work
- UFW needs to allow traffic on wg0 (INPUT chain for local traffic vs FORWARD chain for forwarded traffic)

### Tunnel drops after a few minutes
- Check PersistentKeepalive is set (should be 25)

---

## Key Management

- The server config has: server's private key + client's public key
- The client config has: client's private key + server's public key
- Private keys never leave their machine
- To add a second client: generate a new key pair, add a new [Peer] section to the server config with the new client's public key
- To rotate keys: generate new pairs on both sides, update both configs, restart tunnels