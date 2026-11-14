# 🌐 Hesiko Lab — Autonomous UniFi & Home Assistant SecOps Engine

[![Zero Credentials](https://img.shields.io/badge/Security-Zero%20Credentials-green.svg)](#-zero-credentials-guarantee)
[![Agentic Skills](https://img.shields.io/badge/Skills-Audit%20%7C%20Security%20%7C%20Monitor%20%7C%20Heal-blue.svg)](#-the-4-core-secops-skills)
[![AI Assistants](https://img.shields.io/badge/Compatible-Antigravity%20%7C%20Claude%20%7C%20Cursor-orange.svg)](#-ai-agentic-workflow)

**Hesiko Lab NetSec** is an open-source, security-first automation and orchestration framework designed to make building, auditing, monitoring, and self-healing a high-performance network easy and accessible for everyone.

Built for **Ubiquiti UniFi** ecosystems and **Home Assistant** smart homes, this repository enables AI agents (Antigravity, Claude Code, Cursor, ChatGPT) or human operators to communicate directly with your network, detect vulnerabilities, optimize traffic, and resolve issues autonomously with zero guesswork.

---

## 🔒 Credential Hygiene & Privacy (LLM Data Flow)

This repository is designed to keep credentials out of version control:
- No API keys, passwords, or host IDs are stored in the codebase.
- Credentials and local telemetry dumps (`.env`, `audit_data.json`, `*.json`, `*.pem`, `*.key`) are excluded by [`.gitignore`](file:///.gitignore).
- Setup requires copying [`.env.example`](file:///.env.example) to `.env` and inserting your own **read-only** API key by default.

> [!IMPORTANT]
> **Privacy & LLM Data Flow:** Running `run_audit.py` writes your local network inventory (device models, client hostnames, MAC addresses, SSIDs, and firewall/DNS policies) into `audit_data.json` (passphrases and PSKs are automatically redacted). If you use a cloud LLM (Claude, Gemini, Copilot, ChatGPT), contents of `audit_data.json` that you paste or let the agent read will be sent to that LLM provider. To minimize exposure, redact hostnames/MACs before sharing or run with a local LLM (e.g., Ollama).

---

## 🛠️ The 4 Core SecOps Skills

The framework provides four specialized skills located in [`.agent/skills/`](file:///.agent/skills/):

```
.agent/skills/
├── network-audit/          # Discovers gateways, switches, APs, VLANs, & client inventory
├── network-security/       # Evaluates firewall rules, segmentation, IPS/IDS, & CVE risks
├── network-monitoring/     # Tracks real-time WAN latency, packet drops, & Wi-Fi retry rates
└── network-self-healing/   # PoE port power cycling, safe firewall rollback, & alert dispatch
```

### 1. 🔍 Network Audit (`network-audit`)
- Maps multi-site infrastructure, gateway consoles, PoE switches, and Access Points.
- Discovers subnets, CIDR ranges, DHCP pools, and detects flat network vulnerabilities.
- Inventories all connected wired and wireless clients, isolating unsegmented smart home IoT devices.

### 2. 🛡️ Network Security (`network-security`)
- Evaluates zone-based firewall rules (Classifying rules into: Effective, Shadowed, Redundant, Dead).
- Enforces least-privilege IoT and guest network isolation without breaking smart home discovery (mDNS reflectors).
- Monitors hardware against active CVE advisories (UniFi Gateways, APs, Switches, Home Assistant).
- Delivers structured **Executive Decision Memos** before proposing any configuration modification.

### 3. 📊 Network Monitoring (`network-monitoring`)
- Sifts through live WAN metrics (latency, jitter, uptime, and dual-WAN failover state).
- Detects Wi-Fi RF anomalies (`txRetry > 15%`, co-channel interference, sticky clients).
- Correlates network degradation with Home Assistant smart home sensor availability.

### 4. 🩺 Network Self-Healing (`network-self-healing`)
- **Targeted PoE Power Cycling:** Power-cycles specific switch ports to reboot frozen IoT devices, APs, or cameras remotely without pulling cables.
- **Firewall Rollback Safety:** Takes automatic configuration snapshots prior to policy changes and reverts if management connectivity drops.
- **Alert Dispatch:** Sends real-time event webhooks to Discord, Slack, Telegram, or Home Assistant.

---

## 🤖 AI Agentic Workflow (Antigravity, Claude, & Others)

When an AI agent opens this repository:
1. **Verification:** The agent runs `python3 netsec.py check-env` to test configuration.
2. **Setup Prompting:** If credentials are not yet configured, the agent gently points the user to the Git setup instructions, clearly requesting the necessary keys without technical jargon.
3. **Automated Audit:** Once connected, the agent automatically executes a baseline audit and security evaluation before proposing changes.
4. **Actionable Advice:** The agent formulates clear, opinionated options (`(Recommended)`) and executes self-healing routines upon approval.

---

## 🚀 Quickstart Guide

### 1. Clone the Repository
```bash
git clone https://github.com/hesiko-lab/unifi-secops-mesh.git
cd unifi-secops-mesh
```

### 2. Configure Environment
Copy the example environment file:
```bash
cp .env.example .env
```
Edit `.env` with your preferred editor:
```ini
# UniFi Cloud API Key from https://account.ui.com (Security -> API Keys)
UNIFI_API_KEY=your_unifi_cloud_api_key_here

# Target sites to monitor (or leave blank for all)
TARGET_SITES=all

# Optional Home Assistant connection
HASS_URL=http://homeassistant.local:8123
HASS_TOKEN=your_long_lived_token_here

# Optional alert webhook (Discord / Slack / Telegram)
ALERT_WEBHOOK_URL=
```

### 3. Verify Configuration
```bash
python3 netsec.py check-env
```

### 4. Run Core Operations
```bash
# Run topology and device audit:
python3 netsec.py audit

# Evaluate firewall policies and CVE risk:
python3 netsec.py security

# View real-time WAN & Wi-Fi telemetry:
python3 netsec.py monitor

# Check self-healing status or cycle PoE port:
python3 netsec.py heal --status
python3 netsec.py heal --cycle-poe --switch "USW Flex 2.5G 5" --port 2
```

---

## 📋 Executive Decision Memo Standard

All proposed changes adhere to our decision brief structure:

```markdown
### 🛡️ Decision Required: [Short Title]
- **Site Affected:** [Site Name]
- **Risk Level:** [🔴 High | 🟡 Medium | 🟢 Low / Optimization]
- **Observed Issue:** [Clear 1-2 sentence description of vulnerability or gap]
- **Technical Context:** [Impact on security, lateral movement risk, or performance]

#### Options:
1. **Option A (Recommended):** [Actionable configuration change and benefit]
2. **Option B (Alternative):** [Phased or fallback approach]
3. **Option C (Accept Risk):** [Consequences if no action is taken]

👉 **Recommendation:** [Definitive expert choice and why]
```

---

## 🤝 Contributing & License

Maintained with ❤️ by **Hesiko Lab**.
Contributions, pull requests, and skill enhancements are welcome!
Licensed under the [MIT License](file:///LICENSE).
