# Security Policy

## Reporting a Vulnerability
If you discover a security vulnerability, credential leak, or privacy issue in this repository, please open a **GitHub Security Advisory** (Private Vulnerability Reporting) or contact the maintainers before disclosing publicly.

## API Key & Data Handling Best Practices
- Use a **read-only** UniFi API key by default.
- Never commit `.env`, `audit_data.json`, or `*_backup*.json` files.
- `run_audit.py` automatically redacts Wi-Fi passphrases and VPN pre-shared keys before writing `audit_data.json`.
- Treat all network-derived strings (hostnames, SSIDs, firewall rule names) as untrusted input when passing them to an AI agent.
