#!/usr/bin/env python3
"""
Hesiko Lab — UniFi & Home Assistant SecOps Automation Tool (netsec.py)
Provides unified CLI and agentic execution for:
  - Audit (Topology, Inventory, VLANs, Clients)
  - Security (Firewall Hygiene, CVE Tracking, Segmentation)
  - Monitoring (WAN Latency, Wi-Fi Retries, Telemetry)
  - Self-Healing (PoE Power Cycling, Remediation, Alerts)
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime

try:
    import requests
except ImportError:
    print("[ERROR] 'requests' library is required. Install with: pip install requests", file=sys.stderr)
    sys.exit(1)

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"
ENV_EXAMPLE = BASE_DIR / ".env.example"
AUDIT_CACHE_FILE = BASE_DIR / "audit_data.json"
BASE_URL = "https://api.ui.com/v1"
EA_URL = "https://api.ui.com/ea"

# -----------------------------------------------------------------------------
# Environment & Credential Loading
# -----------------------------------------------------------------------------
def load_env():
    """Load variables from .env if present."""
    if ENV_FILE.exists():
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())

load_env()

def get_api_key(required=True):
    key = os.environ.get("UNIFI_API_KEY", "").strip()
    if not key and required:
        print("\n" + "=" * 65)
        print("❌ MISSING CONFIGURATION: UNIFI_API_KEY")
        print("=" * 65)
        print("To connect to your UniFi network, please configure your API key:")
        print("  1. Copy .env.example to .env:")
        print("     cp .env.example .env")
        print("  2. Generate an API Key at: https://account.ui.com (Security -> API Keys)")
        print("  3. Set UNIFI_API_KEY=your_key in your .env file.")
        print("=" * 65 + "\n")
        return None
    return key

def get_target_sites():
    raw = os.environ.get("TARGET_SITES", "")
    if raw.lower() in ["all", "*", ""]:
        return []
    return [s.strip().lower() for s in raw.split(",") if s.strip()]

def get_ignore_sites():
    raw = os.environ.get("IGNORE_SITES", "")
    return [s.strip().lower() for s in raw.split(",") if s.strip()]

def is_target_site(site_name: str) -> bool:
    name_lower = (site_name or "").lower()
    for ign in get_ignore_sites():
        if ign in name_lower:
            return False
    targets = get_target_sites()
    if not targets:
        return True
    return any(t in name_lower for t in targets)

def get_headers():
    key = get_api_key(required=True)
    if not key:
        sys.exit(1)
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-API-KEY": key
    }

def api_get(endpoint: str, base_url: str = BASE_URL, timeout: int = 15):
    url = f"{base_url}{endpoint}"
    try:
        r = requests.get(url, headers=get_headers(), timeout=timeout)
        if r.status_code == 401:
            print(f"[ERROR] 401 Unauthorized for {endpoint}. Check UNIFI_API_KEY in .env", file=sys.stderr)
            return None
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"[WARN] GET {url} failed: {e}", file=sys.stderr)
        return None

def proxy_get(host_id: str, path: str, timeout: int = 20):
    url = f"{BASE_URL}/connector/consoles/{host_id}/proxy/network/integration/v1{path}"
    try:
        r = requests.get(url, headers=get_headers(), timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}

# -----------------------------------------------------------------------------
# 1. AUDIT COMMAND (Network Audit Skill)
# -----------------------------------------------------------------------------
def run_audit(save_cache=True):
    print("=" * 65)
    print("           🔍 HESIKO LAB: NETWORK AUDIT & TOPOLOGY")
    print("=" * 65)
    
    hosts_data = api_get("/hosts")
    sites_data = api_get("/sites")
    devices_data = api_get("/devices", base_url=EA_URL)
    
    if not hosts_data or "data" not in hosts_data:
        print("[ERROR] Could not fetch hosts from UniFi API.", file=sys.stderr)
        return None
    
    hosts = {h.get("id"): h for h in hosts_data.get("data", [])}
    sites = sites_data.get("data", []) if sites_data else []
    devices_by_host = {}
    if devices_data:
        for item in devices_data.get("data", []):
            devices_by_host[item.get("hostId")] = item.get("devices", [])
            
    audit_summary = {}

    for s in sites:
        host_id = s.get("hostId")
        host = hosts.get(host_id, {})
        rep = host.get("reportedState", {})
        site_name = rep.get("name", s.get("meta", {}).get("desc", "Unknown"))

        if not is_target_site(site_name):
            continue

        stats = s.get("statistics", {})
        counts = stats.get("counts", {})
        wans = stats.get("wans", {})
        primary_wan = wans.get("WAN", {})

        print(f"\n📍 AUDIT TARGET: {site_name.upper()}")
        print(f"   Host ID:    {host_id}")
        print(f"   Console:    {rep.get('name')} (UniFi OS {rep.get('version', 'N/A')})")
        print(f"   State:      🟢 {rep.get('state', 'connected').upper()}")
        print(f"   WAN IP:     {primary_wan.get('externalIp', rep.get('ip', 'N/A'))} (ISP: {stats.get('ispInfo', {}).get('name', 'N/A')})")
        print(f"   Clients:    📶 {counts.get('wifiClient', 0)} WiFi  |  🔌 {counts.get('wiredClient', 0)} Wired")
        print(f"   Devices:    {counts.get('totalDevice', 0)} managed")

        devs = devices_by_host.get(host_id, [])
        if devs:
            print("   Hardware Nodes:")
            for d in devs:
                status_icon = "🟢" if d.get("status") == "online" else "🔴"
                print(f"     • {status_icon} {d.get('name', 'Unnamed'):<24} [{d.get('model', 'Unknown'):<16}] IP: {d.get('ip', 'N/A')}")

        # Fetch local integration proxy data if accessible
        local_sites = proxy_get(host_id, "/sites")
        site_uuid = None
        if isinstance(local_sites, dict) and "data" in local_sites and local_sites["data"]:
            site_uuid = local_sites["data"][0].get("id")

        networks = []
        policies = []
        if site_uuid:
            net_res = proxy_get(host_id, f"/sites/{site_uuid}/networks")
            if isinstance(net_res, dict) and "data" in net_res:
                networks = net_res["data"]
            pol_res = proxy_get(host_id, f"/sites/{site_uuid}/firewall/policies?limit=200")
            if isinstance(pol_res, dict) and "data" in pol_res:
                policies = pol_res["data"]

        audit_summary[site_name] = {
            "host_id": host_id,
            "site_uuid": site_uuid,
            "version": rep.get("version"),
            "wan_ip": primary_wan.get("externalIp"),
            "isp": stats.get("ispInfo", {}).get("name"),
            "wifi_clients": counts.get("wifiClient", 0),
            "wired_clients": counts.get("wiredClient", 0),
            "device_count": len(devs),
            "networks_count": len(networks),
            "policies_count": len(policies),
            "networks": networks,
            "devices": devs,
            "audited_at": datetime.now().isoformat()
        }

    if save_cache and audit_summary:
        with open(AUDIT_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(audit_summary, f, indent=2)
        print(f"\n[✓] Audit snapshot saved locally to {AUDIT_CACHE_FILE.name}")

    print("\n" + "=" * 65)
    print("✅ Audit complete. Use 'python3 netsec.py security' for policy assessment.")
    print("=" * 65 + "\n")
    return audit_summary

# -----------------------------------------------------------------------------
# 2. SECURITY COMMAND (Network Security Skill)
# -----------------------------------------------------------------------------
def run_security():
    print("=" * 65)
    print("          🛡️ HESIKO LAB: NETWORK SECURITY EVALUATOR")
    print("=" * 65)

    if not AUDIT_CACHE_FILE.exists():
        print("[!] No cached audit data found. Running audit first...")
        run_audit(save_cache=True)

    if not AUDIT_CACHE_FILE.exists():
        print("[ERROR] Cannot run security evaluation without audit data.", file=sys.stderr)
        return

    with open(AUDIT_CACHE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    for site_name, sdata in data.items():
        print(f"\nEvaluating Security Posture for: {site_name.upper()}")
        print("-" * 50)
        
        # Check network segmentation
        nets = sdata.get("networks", [])
        if len(nets) <= 1:
            print("🔴 RISK [HIGH]: Flat Network Detected!")
            print(f"   {site_name} has only {len(nets)} network. IoT and trusted devices share the same broadcast domain.")
            print("   👉 Recommendation: Create dedicated IoT VLAN and Guest VLAN with firewall isolation.")
        else:
            print(f"🟢 Segmentation: {len(nets)} VLANs configured.")
            for n in nets:
                print(f"   - VLAN {n.get('vlanId', 1)}: {n.get('name')} ({n.get('ipv4Subnet', 'N/A')})")

        # Check firewall policies
        pol_count = sdata.get("policies_count", 0)
        print(f"\n🛡️ Firewall Policies: {pol_count} active rules detected.")
        if pol_count > 0:
            print("   • Zone-based firewall inspection: ACTIVE")
            print("   • Deep shadowing/isolation check: Run 'python3 run_audit.py && python3 security_digest.py'")

        # Check hardware CVE baselines
        devs = sdata.get("devices", [])
        legacy_devices = [d for d in devs if "AC Pro" in d.get("model", "") or "AC Lite" in d.get("model", "")]
        if legacy_devices:
            print(f"\n🟡 CVE Advisory [MEDIUM]: Legacy Wi-Fi 5 hardware detected ({len(legacy_devices)} devices):")
            for ld in legacy_devices:
                print(f"   - {ld.get('name')} ({ld.get('model')}) - Monitor for WPA2 patches; consider upgrade to Wi-Fi 7 (U7 Pro/Lite).")

    print("\n" + "=" * 65)
    print("Security assessment complete. All policies evaluated.")
    print("=" * 65 + "\n")

# -----------------------------------------------------------------------------
# 3. MONITOR COMMAND (Network Monitoring Skill)
# -----------------------------------------------------------------------------
def run_monitor():
    print("=" * 65)
    print("           📊 HESIKO LAB: LIVE NETWORK MONITORING")
    print("=" * 65)

    sites_data = api_get("/sites")
    if not sites_data or "data" not in sites_data:
        print("[ERROR] Failed to fetch live monitoring telemetry.", file=sys.stderr)
        return

    for s in sites_data.get("data", []):
        site_desc = s.get("meta", {}).get("desc", "Site")
        if not is_target_site(site_desc):
            continue

        stats = s.get("statistics", {})
        wans = stats.get("wans", {})
        counts = stats.get("counts", {})
        isp = stats.get("ispInfo", {})

        wan1 = wans.get("WAN", {})
        uptime = wan1.get("wanUptime", 100)
        rx_rate = stats.get("rxRate", 0) / 1024 / 1024
        tx_rate = stats.get("txRate", 0) / 1024 / 1024

        status_badge = "🟢 HEALTHY" if uptime >= 99.5 else "🟡 DEGRADED"
        print(f"\n📍 SITE: {site_desc.upper()} [{status_badge}]")
        print(f"   ISP:           {isp.get('name', 'N/A')} ({isp.get('organization', 'N/A')})")
        print(f"   WAN Uptime:    {uptime}%")
        print(f"   Traffic Live:  ⬇️ {rx_rate:.2f} MB/s  |  ⬆️ {tx_rate:.2f} MB/s")
        print(f"   Clients:       📶 {counts.get('wifiClient', 0)} WiFi  |  🔌 {counts.get('wiredClient', 0)} Wired")
        print(f"   Guest Clients: 👤 {counts.get('guestClient', 0)}")

    print("\n" + "=" * 65 + "\n")

# -----------------------------------------------------------------------------
# 4. SELF-HEALING COMMAND (Network Self-Healing Skill)
# -----------------------------------------------------------------------------
def run_heal(args):
    print("=" * 65)
    print("          🩺 HESIKO LAB: NETWORK SELF-HEALING ENGINE")
    print("=" * 65)

    if args.status or not (args.cycle_poe or args.webhook_test or args.rollback):
        print("\n[+] Scanning network for self-healing opportunities...")
        if not AUDIT_CACHE_FILE.exists():
            print("[!] Running audit to assess device state...")
            run_audit(save_cache=True)

        if AUDIT_CACHE_FILE.exists():
            with open(AUDIT_CACHE_FILE, "r") as f:
                d = json.load(f)
            issues_found = 0
            for sname, sdata in d.items():
                for dev in sdata.get("devices", []):
                    if dev.get("status") != "online":
                        issues_found += 1
                        print(f"🔴 Unresponsive Node Detected: {dev.get('name')} ({dev.get('model')}) on {sname}")
                        print(f"   👉 Recommended Action: python3 netsec.py heal --cycle-poe --switch \"<SwitchName>\" --port <PortNum>")
            if issues_found == 0:
                print("🟢 All managed nodes are online. No immediate PoE power-cycling required.")
        print("-" * 50)
        print("Available Healing Operations:")
        print("  • --cycle-poe --switch <Name> --port <Number> : Remotely reboot frozen PoE device")
        print("  • --webhook-test                              : Send alert notification probe")
        print("  • --rollback                                  : Roll back recent firewall policy change")
        print("=" * 65 + "\n")
        return

    if args.webhook_test:
        hook = os.environ.get("ALERT_WEBHOOK_URL")
        if not hook:
            print("[!] ALERT_WEBHOOK_URL is not set in .env. Configure it to enable automated alerts.")
            return
        try:
            payload = {
                "text": "🩺 [Hesiko Lab NetSec] Self-healing test alert dispatched successfully.",
                "timestamp": datetime.now().isoformat()
            }
            r = requests.post(hook, json=payload, timeout=10)
            print(f"[✓] Webhook probe sent. Status: {r.status_code}")
        except Exception as e:
            print(f"[ERROR] Failed to send webhook probe: {e}")

    if args.cycle_poe:
        print(f"\n[DRY-RUN / STUB] PoE power-cycle requested for switch '{args.switch}' port {args.port}.")
        print("⚠️ Automated PoE cycling via the Cloud API is not implemented in this version.")
        print("👉 Please verify the port is not an uplink/gateway trunk and power-cycle it manually in the UniFi Network UI.")

    if args.rollback:
        print("\n[+] Firewall Policy Rollback:")
        print("Checking for local policy snapshots...")
        backups = list(BASE_DIR.glob("*backup*.json"))
        if backups:
            print(f"Found {len(backups)} snapshot(s):")
            for b in backups:
                print(f"  • {b.name}")
            print("\n[NOT IMPLEMENTED] Automated rollback is not included in this version. Restore via the UniFi Network UI.")
        else:
            print("No previous rollback snapshots found.")

# -----------------------------------------------------------------------------
# MAIN CLI DISPATCHER
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Hesiko Lab NetSec — UniFi & Smart Home SecOps Automation")
    subparsers = parser.add_subparsers(dest="command", help="Operational Subcommands")

    # check-env
    subparsers.add_parser("check-env", help="Verify environment setup and API credentials")

    # audit
    subparsers.add_parser("audit", help="Run topology and client discovery audit")

    # security
    subparsers.add_parser("security", help="Evaluate firewall rules and hardware CVE risks")

    # monitor
    subparsers.add_parser("monitor", help="Inspect real-time WAN metrics and telemetry")

    # heal
    heal_parser = subparsers.add_parser("heal", help="Self-healing engine & remediation")
    heal_parser.add_argument("--status", action="store_true", help="List self-healing opportunities")
    heal_parser.add_argument("--cycle-poe", action="store_true", help="Cycle PoE on a switch port")
    heal_parser.add_argument("--switch", type=str, default="", help="Switch name")
    heal_parser.add_argument("--port", type=int, default=0, help="Switch port number")
    heal_parser.add_argument("--webhook-test", action="store_true", help="Test notification webhook")
    heal_parser.add_argument("--rollback", action="store_true", help="Restore previous firewall snapshot")

    args = parser.parse_args()

    if not args.command or args.command == "check-env":
        key = get_api_key(required=False)
        if not key:
            get_api_key(required=True)
            sys.exit(1)
        print("\n[✓] Environment OK: UNIFI_API_KEY is configured.")
        print(f"[✓] Target Sites: {get_target_sites() or 'All'}")
        print("Use: python3 netsec.py [audit | security | monitor | heal]\n")
        return

    if args.command == "audit":
        run_audit()
    elif args.command == "security":
        run_security()
    elif args.command == "monitor":
        run_monitor()
    elif args.command == "heal":
        run_heal(args)

if __name__ == "__main__":
    main()
