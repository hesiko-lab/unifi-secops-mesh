#!/usr/bin/env python3
"""
Deep Audit Script for UniFi Multi-Site Deployments.
Queries both Site Manager API and the Cloud Connector Network Application Integration Proxy.
"""

import os
import sys
import json
import requests
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"

if ENV_FILE.exists():
    with open(ENV_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

API_KEY = os.environ.get("UNIFI_API_KEY")
HEADERS = {"Accept": "application/json", "X-API-KEY": API_KEY}
BASE_URL = "https://api.ui.com/v1"

def api_get(endpoint):
    url = f"{BASE_URL}{endpoint}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def proxy_get(host_id, path):
    url = f"{BASE_URL}/connector/consoles/{host_id}/proxy/network/integration/v1{path}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=25)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def audit_site(host_id, host_name):
    print(f"\n[+] Auditing {host_name} (Host ID: {host_id})...")
    res = {"host_name": host_name, "host_id": host_id}

    # 1. Host info
    host_info = api_get(f"/hosts/{host_id}")
    res["host_info"] = host_info

    # 2. Get local sites
    local_sites = proxy_get(host_id, "/sites")
    res["local_sites"] = local_sites

    site_uuid = None
    if local_sites and "data" in local_sites and len(local_sites["data"]) > 0:
        site_uuid = local_sites["data"][0].get("id")
    res["site_uuid"] = site_uuid

    if site_uuid:
        # 3. Networks / VLANs
        res["networks"] = proxy_get(host_id, f"/sites/{site_uuid}/networks")
        # 4. WiFi Broadcasts (strip passphrases/secrets)
        res["wifi"] = redact_secrets(proxy_get(host_id, f"/sites/{site_uuid}/wifi/broadcasts"))
        # 5. Firewall Policies
        res["firewall_policies"] = proxy_get(host_id, f"/sites/{site_uuid}/firewall/policies?limit=200")
        # 6. Firewall Zones
        res["firewall_zones"] = proxy_get(host_id, f"/sites/{site_uuid}/firewall/zones?limit=100")
        # 7. DNS Policies
        res["dns_policies"] = proxy_get(host_id, f"/sites/{site_uuid}/dns/policies")
        # 8. WANs
        res["wans"] = proxy_get(host_id, f"/sites/{site_uuid}/wans")
        # 9. Clients
        res["clients"] = proxy_get(host_id, f"/sites/{site_uuid}/clients")
        # 10. Devices
        res["devices"] = proxy_get(host_id, f"/sites/{site_uuid}/devices")
        # 11. VPN Site to Site (strip PSKs)
        res["vpn_site_to_site"] = redact_secrets(proxy_get(host_id, f"/sites/{site_uuid}/vpn/site-to-site-tunnels"))
        # 12. VPN Servers (strip secrets)
        res["vpn_servers"] = redact_secrets(proxy_get(host_id, f"/sites/{site_uuid}/vpn/servers"))

    return res


SECRET_KEYS = {"x_passphrase", "passphrase", "psk", "presharedkey", "password", "secret", "privatekey"}

def redact_secrets(obj):
    """Recursively redact sensitive credential fields before writing audit_data.json."""
    if isinstance(obj, dict):
        return {
            k: ("[REDACTED]" if k.lower() in SECRET_KEYS else redact_secrets(v))
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [redact_secrets(item) for item in obj]
    return obj

def main():
    hosts_data = api_get("/hosts")
    hosts = hosts_data.get("data", [])
    
    raw_targets = os.environ.get("TARGET_SITES", "")
    targets = [s.strip().lower() for s in raw_targets.split(",") if s.strip()]
    raw_ignore = os.environ.get("IGNORE_SITES", "")
    ignore = [s.strip().lower() for s in raw_ignore.split(",") if s.strip()]

    audit_results = {}
    for h in hosts:
        name = h.get("reportedState", {}).get("name", "")
        host_id = h.get("id")
        name_lower = name.lower()
        if any(ign in name_lower for ign in ignore):
            continue
        if targets and not any(t in name_lower for t in targets):
            continue
        audit_results[name] = audit_site(host_id, name)

    out_file = BASE_DIR / "audit_data.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(audit_results, f, indent=2)
    print(f"\n[OK] Deep audit data dumped to {out_file}")

if __name__ == "__main__":
    main()
