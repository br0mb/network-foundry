# Build Report: CUPS Print Server with Virtual PDF Printer

> **Date:** July 19, 2026
> **Infrastructure:** CUPS print server with virtual PDF printer backend on domain controller

## What Was Built

A CUPS (Common UNIX Printing System) print server with a virtual PDF printer that converts print jobs to PDF files instead of sending them to physical hardware. This provides the full print server management experience — creating print queues, managing permissions, monitoring job status — without requiring a physical printer.

## Configuration Steps

### 1. Install CUPS and PDF Printer Driver
- Installed `cups` and `printer-driver-cups-pdf`
- Started and enabled CUPS service

### 2. Configure Network Access
CUPS defaults to listening on localhost only. Changed `Listen localhost:631` to `Listen 0.0.0.0:631` in `/etc/cups/cupsd.conf` so the web interface is accessible from the network.

### 3. Configure Access Control
Added `Allow from <lab-network>` to the `<Location />`, `<Location /admin>`, and `<Location /admin/conf>` sections in cupsd.conf so lab clients can access the web dashboard.

### 4. Add Admin User to Printer Admin Group
Added the admin user to the `lpadmin` group for CUPS web interface administration.

### 5. Add Virtual PDF Printer
Through the CUPS web interface (Administration → Find New Printers), added the CUPS-PDF virtual printer with the Generic PDF Printer driver.

### 6. Print Test Page
Printed a test page from the CUPS dashboard. Verified the PDF was generated in the user's PDF directory.

## Troubleshooting Issues

### Issue 1: Web Interface Not Reachable
**Cause:** CUPS was listening on `127.0.0.1:631` (localhost only), not on the network interface.
**Fix:** Changed `Listen` directive to `0.0.0.0:631` in cupsd.conf and restarted CUPS.

### Issue 2: "Forbidden" When Accessing Web Interface
**Cause:** CUPS access control only allowed localhost connections.
**Fix:** Added `Allow from <network>` to the Location sections in cupsd.conf.

## Client-Side Printing

From a domain-joined Linux client:
- Installed `cups-client` package
- Listed printers: `lpstat -h <server-ip> -p`
- Printed a file: `lp -h <server-ip> -d <printer-name> <filename>`
- Verified PDF appeared on the server (in the ANONYMOUS directory for unauthenticated print jobs)

## Enterprise Relevance

| Concept | Enterprise Equivalent |
|---------|----------------------|
| CUPS web management | Enterprise print management consoles |
| Virtual PDF printer | Print-to-PDF without physical hardware |
| Network print access | Network printer sharing |
| Access control | Print server permissions |
| Client printing | Remote print queue submission |
| Print job monitoring | Queue status and job tracking |