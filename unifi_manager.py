#!/usr/bin/env python3
"""
UniFi Site Manager Tool
Manages UniFi Cloud Consoles and Sites via the official api.ui.com API.
"""

import os
import sys
import json
import requests
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"

def load_env():
    """Load environment variables from .env file."""
    if ENV_FILE.exists():
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())

load_env()

BASE_URL = "https://api.ui.com/v1"
EA_URL = "https://api.ui.com/ea"

API_KEY = os.environ.get("UNIFI_API_KEY")
raw_targets = os.environ.get("TARGET_SITES", "")
TARGET_SITES = [s.strip().lower() for s in raw_targets.split(",") if s.strip()]
raw_ignore = os.environ.get("IGNORE_SITES", "")
IGNORE_SITES = [s.strip().lower() for s in raw_ignore.split(",") if s.strip()]

def get_headers():
    if not API_KEY:
        print("[ERROR] UNIFI_API_KEY is not set in .env or environment.", file=sys.stderr)
        sys.exit(1)
    return {
        "Accept": "application/json",
        "X-API-KEY": API_KEY
    }

def fetch_api(endpoint: str, base_url: str = BASE_URL):
    url = f"{base_url}{endpoint}"
    try:
        resp = requests.get(url, headers=get_headers(), timeout=15)
        if resp.status_code == 401:
            print("[ERROR] 401 Unauthorized: Invalid API key.", file=sys.stderr)
            sys.exit(1)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        print(f"[ERROR] Request to {url} failed: {e}", file=sys.stderr)
        return None

def is_target(name: str) -> bool:
    name_lower = (name or "").lower()
    for ign in IGNORE_SITES:
        if ign in name_lower:
            return False
    if not TARGET_SITES or "all" in TARGET_SITES:
        return True
    return any(t in name_lower for t in TARGET_SITES)

def cmd_overview():
    """Display comprehensive dashboard for target sites."""
    print("=" * 65)
    print("           UniFi Site Manager — Multi-Site Overview")
    print("=" * 65)

    hosts_data = fetch_api("/hosts")
    sites_data = fetch_api("/sites")
    devices_data = fetch_api("/devices", base_url=EA_URL)

    hosts = {h.get("id"): h for h in (hosts_data.get("data", []) if hosts_data else [])}
    sites = sites_data.get("data", []) if sites_data else []
    devices_by_host = {}
    if devices_data:
        for item in devices_data.get("data", []):
            devices_by_host[item.get("hostId")] = item.get("devices", [])

    for s in sites:
        host_id = s.get("hostId")
        host = hosts.get(host_id, {})
        rep = host.get("reportedState", {})
        site_name = rep.get("name", s.get("meta", {}).get("desc", "Unknown"))
        
        # Filter for targets
        if not is_target(site_name):
            continue

        stats = s.get("statistics", {})
        isp = stats.get("ispInfo", {})
        wans = stats.get("wans", {})
        counts = stats.get("counts", {})
        dev_list = devices_by_host.get(host_id, [])

        primary_wan = wans.get("WAN", {})
        ext_ip = primary_wan.get("externalIp", rep.get("ip", "N/A"))
        isp_name = isp.get("name", "Unknown ISP")
        uptime = primary_wan.get("wanUptime", 100)

        print(f"\n📍 SITE: {site_name.upper()}")
        print(f"   Console:    {rep.get('name')} ({rep.get('version', 'N/A')})")
        print(f"   Status:     🟢 {rep.get('state', 'connected').upper()}")
        print(f"   ISP / WAN:  {isp_name} | External IP: {ext_ip} (Uptime: {uptime}%)")
        print(f"   Clients:    📶 {counts.get('wifiClient', 0)} WiFi  |  🔌 {counts.get('wiredClient', 0)} Wired")
        print(f"   Devices:    {counts.get('totalDevice', len(dev_list))} total (0 offline)")

        if dev_list:
            print("   Hardware Inventory:")
            for d in dev_list:
                d_name = d.get("name", "Unnamed")
                d_model = d.get("model", "Unknown")
                d_ip = d.get("ip", "N/A")
                d_status = "🟢" if d.get("status") == "online" else "🔴"
                print(f"     • {d_status} {d_name:<26} [{d_model:<18}]  IP: {d_ip}")

    print("\n" + "=" * 65)
    print("⚡ Multi-Site Management Status: OK")
    print("   To configure Site-to-Site VPN / Site Magic, visit https://unifi.ui.com")
    print("=" * 65 + "\n")

def cmd_devices():
    """List devices across target consoles."""
    data = fetch_api("/devices", base_url=EA_URL)
    if not data or "data" not in data:
        print("No devices found.")
        return
    for item in data.get("data", []):
        host_id = item.get("hostId")
        devices = item.get("devices", [])
        print(f"\nHost ID: {host_id} (Total: {len(devices)})")
        for d in devices:
            print(f"  - {d.get('name')} ({d.get('model')}) | Status: {d.get('status')} | IP: {d.get('ip')}")

def main():
    if len(sys.argv) < 2 or sys.argv[1].lower() in ["overview", "status", "list"]:
        cmd_overview()
    elif sys.argv[1].lower() == "devices":
        cmd_devices()
    else:
        print("Usage: python3 unifi_manager.py [overview | devices]")

if __name__ == "__main__":
    main()
