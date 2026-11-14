---
name: network-security
description: >-
  Audits and hardens firewall policies, zone segmentation, Threat Management (IPS/IDS),
  guest isolation, and hardware CVE risks across UniFi and smart home environments.
---

# 🛡️ Network Security Skill

The **Network Security Skill** guides the agent to evaluate, audit, and harden network security postures with defense-in-depth principles, zone-based firewall rule analysis, and hardware CVE surveillance.

---

## 1. Core Responsibilities

1. **Zone-Based Firewall Policy Hygiene:**
   - Categorize firewall rules into:
     - **🟢 Effective:** Rules actively enforcing boundary controls (e.g. established/related state returns, DNS/DHCP pinholes, isolate IoT).
     - **🔴 Shadowed / Flawed:** Rules whose intended restriction is bypassed by a preceding or following rule (e.g. restrictive rule followed by default `Allow All Traffic`).
     - **🟡 Redundant:** Rules permitting traffic already allowed by broader zone rules.
     - **⚪ Dead / Inoperative:** Rules referencing empty network IDs or devices in mismatched zones.
2. **IoT & Smart Home Least-Privilege Segmentation:**
   - Ensure IoT VLAN cannot initiate connections to the Trusted/Management LAN.
   - Pinhole only required ports for Home Assistant (e.g. 8123 for HA Web UI, 1883 for MQTT, 5353/udp for mDNS reflector).
   - Isolate Guest network from internal subnets and router gateway access.
3. **Threat Management & DNS Posture:**
   - Verify Intrusion Prevention/Detection System (IPS/IDS) mode and active Suricata rule categories.
   - Verify DNS Shield (DoH / Encrypted DNS) and Content Filtering settings.
4. **Hardware CVE & Vulnerability Tracking:**
   - Actively cross-reference deployed hardware (UniFi Gateways, APs, Switches, Home Assistant Core) against known security advisories (WPA2/3 exploits, dnsmasq, OpenSSL, WireGuard).

---

## 2. Decision Framework (Executive Decision Memo)

Never execute destructive or broad security changes without presenting an **Executive Decision Memo**:

```markdown
### 🛡️ Decision Required: [Short Title]
- **Site Affected:** [Site Name]
- **Risk Level:** [🔴 High | 🟡 Medium | 🟢 Low / Optimization]
- **Observed Issue:** [Clear 1-2 sentence description of vulnerability or gap]
- **Technical Context:** [Impact on security, lateral movement risk, or isolation failure]

#### Options:
1. **Option A (Recommended):** [Actionable configuration change and benefit]
2. **Option B (Alternative):** [Phased or fallback approach]
3. **Option C (Accept Risk):** [Consequences if no action is taken]

👉 **Recommendation:** [Definitive expert choice and why]
```

---

## 3. Tooling
```bash
# Evaluate policies and produce security digest:
python3 netsec.py security
# Or run standalone digest tool:
python3 security_digest.py
```
