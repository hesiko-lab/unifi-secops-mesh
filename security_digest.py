#!/usr/bin/env python3
"""
Security Policy Evaluator & Decision Digest Tool
Evaluates UniFi configurations against cybersecurity best practices and CVE risk profiles.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
AUDIT_FILE = BASE_DIR / "audit_data.json"

ADVISORY_SOURCES = {
    "Ubiquiti Security Advisories": "https://www.ui.com/trust/",
    "UniFi Release Notes": "https://community.ui.com/releases",
}

def load_audit_data():
    if not AUDIT_FILE.exists():
        print("[!] No audit_data.json found. Running run_audit.py first...")
        subprocess.run([sys.executable, str(BASE_DIR / "run_audit.py")], check=False)
    if not AUDIT_FILE.exists():
        print("[ERROR] Failed to load audit data.", file=sys.stderr)
        sys.exit(1)
    with open(AUDIT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def evaluate_site(site_name, data):
    findings = []
    decisions = []

    # 1. Networks / Segmentation
    nets = data.get("networks", {}).get("data", [])
    if len(nets) <= 1:
        findings.append({
            "severity": "HIGH",
            "title": "Flat Network Architecture Detected",
            "desc": f"{site_name} only has {len(nets)} network (Default VLAN 1). All IoT and client devices share the same broadcast domain."
        })
        decisions.append({
            "id": f"{site_name}-VLAN-SEG",
            "priority": "HIGH",
            "title": f"Create Dedicated IoT / Guest VLAN on {site_name}",
            "description": "Smart TVs, IoT appliances, and guest devices currently reside on the same subnet as personal workstations and gateway management.",
            "options": [
                {"choice": "A (Recommended)", "action": "Create a dedicated IoT VLAN (e.g., VLAN 20) with client/device isolation enabled."},
                {"choice": "B", "action": "Enable Guest Hotspot on SSID without separate VLAN."},
                {"choice": "C", "action": "Keep flat network (accept lateral movement risk)."}
            ]
        })

    # 2. WAN & NAT
    host_info = data.get("host_info", {}).get("data", {})
    if not host_info:
        host_info = data.get("host_info", {})
    rep = host_info.get("reportedState", {})
    wans = rep.get("wans", [])
    primary_wan = next((w for w in wans if w.get("type") == "WAN"), {})
    ipv4 = primary_wan.get("ipv4", "")

    if ipv4.startswith("192.168.") or ipv4.startswith("10.") or ipv4.startswith("172.16."):
        findings.append({
            "severity": "MEDIUM",
            "title": "Double NAT on Primary WAN",
            "desc": f"Primary WAN interface received private IP {ipv4}. Upstream ISP router is performing NAT."
        })
        decisions.append({
            "id": f"{site_name}-DOUBLE-NAT",
            "priority": "MEDIUM",
            "title": f"Resolve Double NAT on {site_name}",
            "description": f"The gateway WAN interface has private IP {ipv4}. Double NAT adds latency jitter and complicates inbound routing.",
            "options": [
                {"choice": "A (Recommended)", "action": "Configure the UniFi gateway WAN MAC as the DMZ Host in your ISP router portal."},
                {"choice": "B", "action": "Request a bridge-mode / modem-only device from your ISP."},
                {"choice": "C", "action": "Leave as-is (SD-WAN / Site Magic handles outbound NAT traversal automatically)."}
            ]
        })

    # 3. Wi-Fi Security
    wifis = data.get("wifi", {}).get("data", [])
    for w in wifis:
        sec = w.get("securityConfiguration", {})
        proto = sec.get("protocol")
        if proto == "WPA2":
            findings.append({
                "severity": "LOW",
                "title": f"Wi-Fi SSID '{w.get('name')}' using WPA2 only",
                "desc": "Consider enabling WPA2/WPA3 transition mode for enhanced handshake protection on supported devices."
            })

    # 4. Hardware Lifecycle Advisory Check
    devs = data.get("devices", {}).get("data", [])
    legacy_devices = []
    for d in devs:
        model = d.get("model", "")
        if "AC Pro" in model or "AC Lite" in model:
            legacy_devices.append(d.get("name"))

    if legacy_devices:
        findings.append({
            "severity": "INFO",
            "title": f"Legacy Wi-Fi 5 Hardware: {', '.join(legacy_devices)}",
            "desc": f"Verify firmware against official Ubiquiti advisories ({ADVISORY_SOURCES['Ubiquiti Security Advisories']}) and consider upgrading to Wi-Fi 6/7."
        })

    # 5. Firewall Policy Hygiene & Shadowing Evaluation
    policies = data.get("firewall_policies", {}).get("data", [])
    zones_list = data.get("firewall_zones", {}).get("data", [])
    zones_map = {z.get("id"): z.get("name") for z in zones_list}
    zone_nets = {z.get("name"): z.get("networkIds", []) for z in zones_list}

    if policies:
        dead_count = 0
        shadowed_count = 0
        redundant_count = 0
        effective_count = 0

        from collections import defaultdict
        zone_pairs = defaultdict(list)
        for r in policies:
            src_n = zones_map.get(r.get("source", {}).get("zoneId"), "UNKNOWN")
            dst_n = zones_map.get(r.get("destination", {}).get("zoneId"), "UNKNOWN")
            zone_pairs[f"{src_n} -> {dst_n}"].append(r)

        for pair, rlist in zone_pairs.items():
            src_z, dst_z = pair.split(" -> ")
            src_empty = len(zone_nets.get(src_z, [])) == 0 and src_z not in ["External", "Gateway"]
            dst_empty = len(zone_nets.get(dst_z, [])) == 0 and dst_z not in ["External", "Gateway"]
            rlist.sort(key=lambda x: x.get("index", 0))
            bottom_rule = rlist[-1]
            bottom_act = bottom_rule.get("action", {}).get("type")

            for r in rlist:
                r_name = r.get("name", "Unnamed")
                r_idx = r.get("index")
                act = r.get("action", {}).get("type")

                if src_empty or dst_empty:
                    dead_count += 1
                elif bottom_act == "ALLOW" and r_idx < bottom_rule.get("index") and act == "ALLOW":
                    # If an earlier ALLOW rule is followed by a catch-all ALLOW, it may be redundant or indicate missing default-deny
                    if r.get("trafficFilter") or r.get("destination", {}).get("portMatchingType") == "SPECIFIC":
                        shadowed_count += 1
                        findings.append({
                            "severity": "HIGH",
                            "title": f"Potential Firewall Policy Shadowing ({pair}): '{r_name}' (#{r_idx})",
                            "desc": f"Restrictive allow rule #{r_idx} is followed by a bottom catch-all ALLOW rule (#{bottom_rule.get('index')}). Verify whether default-deny should be enforced."
                        })
                        decisions.append({
                            "id": f"{site_name}-FW-SHADOW-{r_idx}",
                            "priority": "HIGH",
                            "title": f"Review Catch-All ALLOW on {pair}",
                            "description": f"Rule '{r_name}' (#{r_idx}) precedes a catch-all ALLOW rule (#{bottom_rule.get('index')}), which permits all other traffic.",
                            "options": [
                                {"choice": "A (Recommended)", "action": f"Change {pair} default zone action from 'Allow' to 'Block/Drop' if only whitelisted ports should pass."},
                                {"choice": "B", "action": f"Add an explicit 'Block All' rule directly below '{r_name}'."},
                                {"choice": "C", "action": "Accept risk if unrestricted traffic is intentional."}
                            ]
                        })
                    else:
                        redundant_count += 1
                else:
                    effective_count += 1

        findings.append({
            "severity": "INFO",
            "title": f"Zone Firewall Hygiene: {len(policies)} Policies Analyzed",
            "desc": f"Effective: {effective_count} | Shadowed/Flawed: {shadowed_count} | Redundant: {redundant_count} | Dead/Inoperative: {dead_count}"
        })

    return findings, decisions

def main():
    print("=" * 65)
    print("        UniFi Security Policy & CVE Decision Digest")
    print("        Timestamp:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 65)

    data = load_audit_data()
    all_decisions = []

    for name in sorted(data.keys()):
        if name in data:
            print(f"\n📍 AUDIT FINDINGS: {name.upper()}")
            findings, decisions = evaluate_site(name, data[name])
            all_decisions.extend(decisions)
            
            if not findings:
                print("  🟢 Zero security anomalies found.")
            for f in findings:
                icon = "🔴" if f["severity"] == "HIGH" else "🟡" if f["severity"] == "MEDIUM" else "ℹ️"
                print(f"  {icon} [{f['severity']}] {f['title']}")
                print(f"     {f['desc']}")

    print("\n" + "=" * 65)
    print("📋 DECISIONS FOR THE ADMINISTRATOR:")
    print("=" * 65)

    if not all_decisions:
        print("🟢 No urgent administrative decisions pending. Both sites are healthy.")
    else:
        for idx, dec in enumerate(all_decisions, 1):
            print(f"\n[{idx}] 🛡️ {dec['title']} (Priority: {dec['priority']})")
            print(f"    Context: {dec['description']}")
            print("    Choices:")
            for opt in dec["options"]:
                print(f"      • Option {opt['choice']}: {opt['action']}")

    print("\n" + "=" * 65 + "\n")

if __name__ == "__main__":
    main()
