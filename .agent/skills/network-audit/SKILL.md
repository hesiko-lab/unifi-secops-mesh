---
name: network-audit
description: >-
  Audits UniFi and smart home infrastructure topology, VLAN segmentation, connected clients,
  hardware inventory, and firmware drift across multi-site networks.
---

# 🔍 Network Audit Skill

The **Network Audit Skill** equips the agent to perform comprehensive, non-destructive discovery and topology auditing across Ubiquiti UniFi consoles and connected smart home infrastructure (such as Home Assistant).

---

## 1. Scope & Capabilities
1. **Topology & Hardware Inventory:**
   - Detect and classify UniFi Gateways (UDM-Pro/SE, UDR, UCG-Ultra, CloudKey), Switches (USW Flex, USW Ultra, PoE switches), and Access Points (Wi-Fi 7, Wi-Fi 6, Wi-Fi 5).
   - Track firmware versions and compare against latest vendor release baselines.
2. **VLAN & Subnet Discovery:**
   - Identify configured networks, CIDR blocks, DHCP ranges, and gateway IP addresses.
   - Detect flat network architectures (e.g. single Default VLAN 1) versus segmented multi-VLAN layouts (LAN, IoT, Guest, Cameras, Management).
3. **Client Classification & Inventory:**
   - Map active wired and wireless clients.
   - Flag unsegmented smart home IoT devices (Shelly, ESPHome, Sonoff, Tuya, Philips Hue, Sonos, smart TVs) dwelling in trusted networks.
   - Pinpoint Home Assistant host location and its reachability across subnets.
4. **Site Drift Analysis:**
   - Compare multi-site deployments (e.g. Site A vs. Site B) to detect policy and configuration discrepancies.

---

## 2. Execution Workflow

When an audit is requested:
1. **Verify Credentials:** Ensure `UNIFI_API_KEY` is present. If missing, guide the user to obtain an API key from [unifi.ui.com](https://unifi.ui.com) -> API Keys.
2. **Execute Data Collection:**
   ```bash
   python3 netsec.py audit
   # Or run deep collector:
   python3 run_audit.py
   ```
3. **Synthesize Findings:**
   - Present a concise inventory table (Gateways, Switches, APs, Total Clients).
   - Highlight any unsegmented IoT devices or flat-network risks.
   - Generate or update `AUDIT_REPORT.md` with timestamps and structural summaries.
