---
name: network-self-healing
description: >-
  Provides autonomous and user-guided self-healing: PoE power cycling for hung devices,
  safe firewall rollback mechanisms, Wi-Fi channel healing, and automated alert dispatch.
---

# 🩺 Network Self-Healing Skill

The **Network Self-Healing Skill** equips the agent to perform both automated and assisted remediation routines to resolve network degradation, unresponsive devices, and failed configurations safely without causing downtime.

---

## 1. Core Self-Healing Capabilities

1. **Targeted PoE Port Power Cycling:**
   - Detect unresponsive PoE-powered devices (UniFi Protect cameras, Access Points, Home Assistant hubs, VoIP phones).
   - Execute a safe, controlled PoE power cycle on the exact switch port to hard-reboot the device remotely without physical access.
2. **Safe Firewall Rollback & Safety Clocks:**
   - When modifying firewall or zone policies, always take an automated backup before applying changes.
   - Run connectivity verification probes post-change. If the management proxy or local gateway connection fails, automatically trigger rollback to the last verified policy configuration.
3. **RF Channel & Interference Healing:**
   - Detect severe Wi-Fi channel overlap or radar DFS events.
   - Advise or trigger channel re-optimization during low-traffic windows.
4. **Smart Home Entity Recovery:**
   - Trigger Home Assistant integration reloads or host restart routines if the API or bridge becomes unresponsive.
5. **Alert & Event Webhook Dispatch:**
   - Send structured event notifications to Discord, Slack, Telegram, or Home Assistant when self-healing actions are initiated or resolved.

---

## 2. Safety Rules & Guardrails
- **Zero Blind Reboots:** Always identify the specific switch name, port number, and connected device MAC/IP before triggering a PoE cycle.
- **Critical Device Protection:** Never power cycle gateway uplink ports or switch interconnect trunks.
- **User Confirmation Prompt:** For high-impact actions, prompt the user with an Executive Decision Memo or quick confirmation before rebooting network core equipment.

---

## 3. Tooling
```bash
# Check healing opportunities and unresponsive devices:
python3 netsec.py heal --status

# Power cycle a specific switch port safely:
python3 netsec.py heal --cycle-poe --switch "Switch-Name" --port 3

# Rollback last firewall changes if needed:
python3 netsec.py heal --rollback-firewall
```
