# GitHub Copilot & AI Agent Instructions — UniFi SecOps Mesh

Welcome! **UniFi SecOps Mesh** is an autonomous UniFi & Home Assistant SecOps framework.

## Quickstart for AI Agents (Antigravity, Claude Code, GitHub Copilot, Cursor)
1. Read `AGENTS.md` / `CLAUDE.md` / `GEMINI.md` and the skills in `.agent/skills/`:
   - `network-audit/SKILL.md`
   - `network-monitoring/SKILL.md`
   - `network-security/SKILL.md`
   - `network-self-healing/SKILL.md`
   - `unifi-secops-advisor/SKILL.md`
2. Configure `.env` from `.env.example` (never commit `.env` or `audit_data.json`).
3. Run `python3 netsec.py check-env` followed by `python3 run_audit.py` and `python3 security_digest.py`.

## Strict Security & Anonymity Rules
- **NEVER** commit `.env`, `audit_data.json`, real site names, internal IPs, MAC addresses, or `UNIFI_API_KEY` / `HASS_TOKEN` values.
- All PRs and pushes are checked by `.github/workflows/dlp-guard.yml`.
