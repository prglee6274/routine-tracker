# Context papers — field-defining work NOT at the 9 watched venues

These are not from USENIX / S&P / NDSS / CCS / ACSAC / RAID / ESORICS / AsiaCCS / DSN, so they are deliberately excluded from the main index. But a related-work section on Electron-app vulnerabilities is incomplete without acknowledging them. Treat them as **context / motivation**, and be precise about their venue type (journal, industry talk, or preprint) when citing.

## Electrolint and security of electron applications
- **Venue / type:** *Array* (Elsevier open-access journal), 2021 — peer-reviewed journal, not a top security conference.
- **Link:** https://www.sciencedirect.com/science/article/pii/S2667295221000222
- **Why it matters:** the most-cited non-top-venue academic work specifically on Electron security. Surveys client-side vulnerability classes in Electron apps (XSS, clickjacking, DOM clobbering) and proposes a lint-style static checker.
- **How to cite:** as earlier academic attention to Electron-specific weaknesses and a lightweight static-analysis precursor to the heavier systems (DOM-tree type, Inspectron, COINDEF).

## ElectroVolt: Pwning popular desktop apps while uncovering new attack surface on Electron
- **Venue / type:** Black Hat USA 2022 / DEF CON 30 — **industry/practitioner** research, not peer-reviewed.
- **Link:** https://www.blackhat.com/us-22/briefings/schedule/
- **Why it matters:** demonstrated real 1-click RCE exploit chains against Discord, Microsoft Teams, VS Code, and Element. The most cited real-world impact evidence in this space.
- **How to cite:** as practitioner evidence that Electron XSS→RCE is not theoretical — strong motivation in an intro/threat-model section. Label it as industry research, not an academic paper.

## Developers Are Victims Too: A Comprehensive Analysis of the VS Code Extension Ecosystem
- **Venue / type:** arXiv preprint, 2024 (arXiv:2411.07479) — confirm any venue acceptance before citing as published.
- **Link:** https://arxiv.org/abs/2411.07479
- **Why it matters:** security of the VS Code (an Electron app) extension marketplace — supply-chain risk one layer above the framework.

## JavaSith: A Client-Side Framework for Analyzing Potentially Malicious Extensions in Browsers, VS Code, and NPM Packages
- **Venue / type:** arXiv preprint, 2025 (arXiv:2505.21263) — verify status before citing.
- **Link:** https://arxiv.org/abs/2505.21263
- **Why it matters:** client-side analysis spanning browsers, VS Code, and npm — adjacent tooling for the same threat surface.

---

_If any of these is later accepted at a watched venue, move it into `papers/` as a full note and add an `in_scope` ledger entry._
