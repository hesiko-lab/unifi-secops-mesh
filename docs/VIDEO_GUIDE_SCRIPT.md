# 🎬 UniFi SecOps Mesh — Video Walkthrough & Quickstart Script (5 Minutes)

Use this script to record a community quickstart video for YouTube or the Ubiquiti / Home Assistant Community.

## 0:00 – 0:45 | Introduction
- **Visual**: Show `README.md` architecture diagram and `.agent/skills/`.
- **Narration**: "Managing UniFi networks and Home Assistant IoT segmentation manually is error-prone. UniFi SecOps Mesh gives your AI coding agent 5 specialized SecOps skills to audit, monitor, and harden your network."

## 0:45 – 2:00 | Safe Setup (Zero-Leak Configuration)
- **Visual**: Show `cp .env.example .env` and `python3 netsec.py check-env`.
- **Narration**: "Your `UNIFI_API_KEY` and `HASS_TOKEN` stay strictly inside `.env`, which is gitignored alongside `audit_data.json`."

## 2:00 – 3:30 | Running Your First Multi-Site Audit
- **Visual**: Run `python3 run_audit.py` and `python3 security_digest.py`.
- **Narration**: "In seconds, you get a prioritized Executive Decision Memo highlighting flat networks, IoT devices on trusted VLANs, firewall rule drift, and pending firmware CVEs."

## 3:30 – 4:30 | Agentic Quickstart (Antigravity, Claude, Copilot)
- **Visual**: Open `.agent/skills/unifi-secops-advisor/SKILL.md`.
- **Narration**: "Point Antigravity, Claude Code, or GitHub Copilot at this repo and ask for a security audit—your agent immediately knows the exact UniFi Cloud Connector endpoints and Zone-Based Firewall best practices."

## 4:30 – 5:00 | Outro
- **Visual**: `https://github.com/hesiko-lab/unifi-secops-mesh`
- **Narration**: "Star the repo, fork it for your own homelab, and never commit your `.env` or `audit_data.json`!"
