# Changelog

## 2026-06-04 — Daily watch

Swept all 9 venues (web search + accepted-paper HTML). Fetched & grepped the NDSS 2026 and IEEE S&P 2026 accepted-paper pages in full; IEEE S&P 2026 had no in-scope hits. Targeted searches covered USENIX Sec '25, CCS '25, ACSAC/RAID/ESORICS '25, AsiaCCS '26, DSN '25.

Added **3 in-scope notes** (all ADJACENT — Node.js-runtime / npm side of the Electron threat model; gaps left by the backfill's Electron-only sweep):
- **NDSS 2026 — Bullseye** (Houis et al.) — dynamic detection of prototype pollution in npm packages; 290 zero-days / 149 CVEs across ~50k packages, no false positives. Discovery tool for the XSS→RCE escalation primitive Electron apps inherit.
- **ACM CCS 2023 — HODOR** (Wang et al.) — seccomp syscall-whitelisting shrinks Node.js attack surface to 19.42% avg, <3% overhead. Backfill miss; sibling to Mininode.
- **ACM CCS 2025 — NodeShield** (Cornelissen & Balliu) — runtime SBOM+capability (CBOM) enforcement; blocks 98.51% of 67 known supply-chain attacks, <1ms overhead. (Balliu also co-authored Silent Spring.)

Recorded **3 new excluded** (NDSS 2026, matched a keyword but out of scope): Cross-Boundary Mobile Tracking (mobile WebView), From Noise to Signal (generic npm SCA), FirmCross (firmware C-Lua hybrid web services).

Grounding: all 3 notes from open-access full text (Concordia author PDF for Bullseye; arXiv preprints for HODOR & NodeShield). Ledger now 9 in-scope / 8 excluded / 4 context. Note: the parent `.git` is not mounted in this sandbox, so the scoped commit must be run on the user's machine.

## 2026-06-02 — Initial backfill (2020 → present)

Swept all 9 watched venues (USENIX Security, IEEE S&P, NDSS, CCS, ACSAC, RAID, ESORICS, AsiaCCS, DSN) for 2020–2026.

Added **6 in-scope notes**:
- NDSS 2023 — DOM-tree type (Jin et al.) — PRIMARY
- CCS 2022 — XRCE / XGuard (Xiao et al.) — PRIMARY
- USENIX Security 2024 — Inspectron (Ali et al.) — PRIMARY
- IEEE S&P 2025 — COINDEF (Yang et al.) — PRIMARY
- USENIX Security 2023 — Silent Spring (Shcherbakov et al.) — ADJACENT
- RAID 2020 — Mininode (Koishybayev & Kapravelos) — ADJACENT

Recorded **5 excluded** (at a watched venue but out of scope) and **4 context** papers (field-defining work outside the 9 venues).

Key finding: the topic is concentrated at the top-4 venues; the 1.5-tier venues are effectively empty on Electron-app vulnerabilities (only Mininode at RAID, and it targets server-side Node.js).

Grounding: all notes built from full text except CCS 2022 (ACM paywalled → abstract + secondary sources, flagged in-note).
