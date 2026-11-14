---
name: unifi-secops-advisor
description: >-
  Audits UniFi multi-site networks, tracks hardware CVEs, evaluates firewall/VLAN policies,
  sifts through alerts and metrics, and produces actionable decision briefs for network administrators.
---

# UniFi SecOps Advisor Skill

This skill equips the agent to act as a proactive, autonomous Senior Network Security Engineer and Auditor for UniFi multi-site deployments (e.g., **Site A** and **Site B**).

---

## 1. Core Operating Principles

1. **Defense-in-Depth Assessment:**
   - Always verify Threat Management (IPS/IDS) status, active rule categories, and inspection posture across all sites.
   - Audit network segmentation: No production environment should run on a flat network without an isolated IoT/Smart device VLAN.
   - Enforce least-privilege firewall rules: Drop invalid packets, isolate guest networks, filter mDNS to necessary reflector ports (5353/udp), and restrict inter-VLAN routing.

2. **CVE & Hardware Vulnerability Surveillance:**
   - Actively monitor the specific hardware stack present in the sites:
     - **Gateways:** UniFi Dream Router 7 (`UDR7`), UniFi OS v5.1.x
     - **Switches:** `US 8 60W`, `USW Flex 2.5G 5`, `USW Ultra 60W`
     - **Access Points:** `U7 Lite` (Wi-Fi 7), `U6 LR` (Wi-Fi 6), `FlexHD` (Wi-Fi 5), `AC Pro` (Wi-Fi 5 legacy)
   - Cross-reference known Ubiquiti advisories (e.g. Ubiquiti Community Release Notes, NVD / CVE databases for dnsmasq, hostapd, OpenSSL, WireGuard, and Suricata).

3. **Log & Anomaly Sifting:**
   - Parse WAN latency spikes, packet loss, and WAN failover logs.
   - Review high Wi-Fi retry rates (`txRetry` > 15%).
   - Detect and flag Double NAT configurations and recommend ISP modem bridge/DMZ steps.

---

## 2. Decision Framework (How to Present to User)

When recommending changes, do NOT just dump raw logs. Present an **Executive Decision Memo** structured as:

```markdown
### 🛡️ Decision Required: [Short Title]
- **Site Affected:** [Site A / Site B]
- **Risk Level:** [🔴 Critical | 🟡 Medium | 🟢 Low / Optimization]
- **Observed Issue:** [Clear 1-2 sentence description of vulnerability or gap]
- **Technical Context:** [Why this matters, e.g. lateral movement, double NAT latency]

#### Options:
1. **Option A (Recommended):** [Actionable steps and benefit]
2. **Option B (Alternative):** [Fallback or phased approach]
3. **Option C (Accept Risk):** [Consequences if no action is taken]

👉 **Recommendation:** [Your definitive expert choice and why]
```

---

## 3. Routine Audit Procedure

1. Run `python3 unifi_manager.py` to verify general host connectivity and WAN IP integrity.
2. Run `python3 run_audit.py` to fetch deep configurations via the Cloud Connector Proxy into `audit_data.json` (always enforce `?limit=200` on policies to avoid 25-rule default pagination truncation).
3. Compare policies across sites to identify drift (e.g. Site A has segmented VLANs & zone policies; Site B has a default flat VLAN).
4. Run policy hygiene analysis to classify rules into Effective, Shadowed, Redundant, and Dead.
5. Check firmware release notes for any pending CVEs or critical bug fixes.
6. Produce the updated `AUDIT_REPORT.md` and present new decision points.

---

## 4. Zone-Based Firewall Policy & Counter Evaluation Methodology

When auditing UniFi OS 5.1.x Zone-Based Firewall architectures:

1. **Pagination Awareness:**
   - The `/firewall/policies` API defaults to a page limit of 25. Always query with `?limit=200` to capture all rules across all 35 zone pairs.

2. **Counter & Telemetry Constraints in UniFi OS 5.1.x:**
   - The Cloud Connector Integration API provides structural metadata, rule order (`index`), `connectionStateFilter`, `trafficFilter`, and `loggingEnabled`, but does NOT embed active runtime packet/byte counters inside the policy payload (legacy USG `/stat/fwrule` is deprecated/404 on modern UniFi OS gateways).
   - Rules with `loggingEnabled: True` emit syslog events on matches. Rules with `loggingEnabled: False` run silently in kernel `nftables`.
   - Flow auditing must combine stateful structural path analysis, endpoint-to-zone topology mapping, and index evaluation.

3. **Classification Categories:**
   - **🟢 Effective (In-Use):** Rules that actively process and enforce traffic control on live interfaces (e.g. stateful returns, DNS/DHCP pinholes, mDNS reflection, drops on boundary edges).
   - **🔴 Shadowed / Flawed:** Rules whose intended security effect is negated by a subsequent or preceding rule. 
     *Critical Pattern:* If a restrictive rule (e.g. allowing only specific ports from DMZ to External) is followed by a default `Allow All Traffic` rule (`INT_MAX`), all non-whitelisted ports pass through anyway.
   - **🟡 Redundant:** Rules that explicitly permit traffic that would already be allowed by a broader rule in the same zone pair (e.g. allowing specific Google ad domains from Internal to External when the zone policy already has `Allow All Traffic` with `allowReturnTraffic: True`).
   - **⚪ Dead / Inoperative:**
     - *Orphaned Zone:* Any rule attached to a zone that has no assigned VLANs or interfaces (`networkIds: []`, e.g., an unassigned `Hotspot` zone).
     - *Topology Mismatch:* Rules where the target device MAC/IP does not reside in the source zone (e.g., Home Assistant located on `Internal` while the rule is bound to `Dmz -> Internal`).

