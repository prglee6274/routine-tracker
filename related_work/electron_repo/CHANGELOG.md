# Changelog

## 2026-06-05 — Daily watch

Swept all 9 venues (web search + accepted-paper HTML). Re-grepped the IEEE S&P 2026 accepted list with broader scope terms (not just "electron"), and fully read both AsiaCCS 2026 cycle-1/cycle-2 lists. The USENIX Sec '26 cycle-1 page is client-rendered and returned empty via web_fetch (no browser connected this run) → covered via targeted web search instead. CCS '26 / DSN '26 / ESORICS / RAID / ACSAC searches returned no new in-scope hits.

Added **3 in-scope notes** (all ADJACENT — Node.js-runtime / V8-embedder side of the Electron threat model):
- **IEEE S&P 2026 — GASKET, "Best of Both Worlds"** (Alexopoulos, Sotiropoulos, Su, Mitropoulos) — dynamic JS→native/Wasm *bridge* identification via V8 function-object memory layout; perfect recall / 0 FP, +2.5× bridges → **54** missed vulnerable flows (**19** exploitable) across **1,266** npm packages. New this cycle; the prior run's S&P'26 grep missed it because the paper never says "Electron" (it targets Node.js/Deno/Chromium embedders).
- **USENIX Security 2024 — GHunter** (Cornelissen, Shcherbakov, Balliu) — dynamic taint analysis built into V8/Node.js/Deno; **56** Node.js + **67** Deno universal prototype-pollution gadgets (ACE 19, priv-esc 31, path-traversal 13), incl. CVE-2023-31414 RCE from a bad gadget fix. Backfill miss; sibling to Silent Spring.
- **NDSS 2025 — NodeMedic-FINE** (Cassel, Sabino, Hsu, Martins, Jia) — type/object-structure-aware fuzzing + SMT exploit synthesis for ACE/ACI in npm; **2,257** flows and **766** auto-synthesized working exploits across **33,011** sink-containing packages. Backfill miss.

Recorded **1 new excluded**: AsiaCCS 2026 — "Original Sin of npm" (generic npm dependency-network vulnerability-propagation measurement; not Electron/Node-runtime-discovery specific). Out-of-venue items deliberately skipped: "Unveiling the Invisible / Dasty" (WWW'24) and "Learning to Triage Taint Flows" (arXiv, no confirmed venue).

Grounding: all 3 notes from open-access full text (author S&P PDF for GASKET; arXiv for GHunter; NDSS PDF for NodeMedic-FINE). Ledger now **12 in-scope / 9 excluded / 4 context**. Parent `.git` is one level above the mounted `related_work` folder and may not be reachable in this sandbox; the scoped commit was attempted via `scripts/commit_and_push.sh` (push fails offline — expected).

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
