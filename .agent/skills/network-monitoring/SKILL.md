---
name: network-monitoring
description: >-
  Monitors live network health, WAN latency/packet loss, Wi-Fi retry rates, channel congestion,
  and client connectivity telemetry across UniFi and Home Assistant.
---

# 📊 Network Monitoring Skill

The **Network Monitoring Skill** empowers the agent to sift through live telemetry, track connectivity health, detect anomalies before they cause user disruptions, and correlate network events with smart home performance.

---

## 1. Key Metrics & Detection Thresholds

1. **WAN & ISP Health:**
   - **Latency:** Flag latency spikes (> 50ms on fiber/cable).
   - **Packet Loss:** Detect packet loss > 1.5% or interface flapping.
   - **Multi-WAN & Failover:** Monitor secondary WAN state (e.g. backup LTE/5G or dual ISP) and report failover events.
   - **Double NAT Detection:** Detect private IP assignments on WAN interfaces and advise on ISP modem bridge/DMZ mode.
2. **Wi-Fi Performance & RF Telemetry:**
   - **Tx Retry Rate (`txRetry`):** Flag access points or SSIDs with `txRetry > 15%`.
   - **Channel Congestion:** Identify co-channel interference on 2.4 GHz and 5 GHz bands.
   - **Client RSSI & Roaming:** Identify sticky clients with weak signals (< -75 dBm) causing overall airtime degradation.
3. **Smart Home Entity & Device Health:**
   - Track Home Assistant network state, unavailable smart home entities, and high-frequency disconnects on 2.4 GHz IoT Wi-Fi networks.

---

## 2. Monitoring Workflow

1. **Fetch Live Metrics:**
   ```bash
   python3 netsec.py monitor
   ```
2. **Analyze Anomalies:**
   - Group findings by severity (Critical, Warning, Informational).
   - Correlate Wi-Fi retries with physical AP placement or IoT device density.
3. **Notify / Log:**
   - If `ALERT_WEBHOOK_URL` is configured, dispatch summary events for critical anomalies.
   - Advise the user on actionable adjustments (channel tuning, AP power adjustments, or triggering self-healing).
