# Changelog

## 2026-06-08 — Daily watch

**No new papers today.** Swept all 9 venues (web search across the standing queries; web_fetch on accepted-paper HTML).

Notable this run: the **USENIX Sec '26 Cycle 1 accepted-papers page now renders via web_fetch** (123 KB / 778 lines; in prior runs it returned empty as a client-rendered shell). Fully grepped it for the in-scope vocabulary (electron / nodeintegration / preload / contextbridge / context isolation / renderer / chromium / node.js / desktop app / prototype pollution / webview) → **zero in-scope hits** (control term "attack" matched 47×, confirming the grep ran against real content, not an empty shell; Cycle 1 is dominated by LLM/ML, MPC/crypto, MIA and phishing work). **USENIX Sec '26 Cycle 2** acceptances still not public (final papers due Jun 11; symposium Aug 12–14, 2026). **CCS '26** accepted list still not public (only the Cycle A acceptance-rate stat — 19.5% of the 981-paper final pool — and the between-cycle transparency report are out). **AsiaCCS '26** Cycle 1 & 2 lists (released Apr 26, fully grepped in prior runs) unchanged — the only near-scope hit "Original Sin of npm" is already in `excluded[]`. **IEEE S&P '26 / NDSS '26** (fully grepped in prior runs) and **ACSAC / RAID / ESORICS / DSN '26** surfaced no new in-scope hits. Every in-scope academic result that appeared is already in the ledger (DOM-tree type, Inspectron, COINDEF, Silent Spring, Mininode, HODOR, NodeShield, Bullseye, GASKET, GHunter, NodeMedic-FINE, XRCE/XGuard).

The 2026 Electron surface that searches returned remains **CVE disclosures and industry write-ups**, not peer-reviewed top-venue papers: CVE-2026-34780 (context-isolation bypass via contextBridge WebCodecs VideoFrame transfer, CVSS 8.4), CVE-2026-34725 (dbgate-web stored XSS→RCE under nodeIntegration:true/contextIsolation:false), CVE-2026-42090 (Notesnook stored XSS→RCE on export, CVSS 9.6), the DeepChat openExternal-via-XSS RCE, and the "Breaking the App Shell: Five New Electron Vulnerabilities" round-up. Consistent with prior out-of-venue handling these are **not** added to `excluded[]` (which tracks watched-venue papers only); they remain useful as fresh motivation/impact citations.

Ledger unchanged: **12 in-scope / 9 excluded / 4 context**. Scoped commit attempted via `scripts/commit_and_push.sh`; in this sandbox the parent `.git` sits one level above the mounted `related_work` folder and is not reachable, so the commit must be completed on the user's machine (push is offline-expected regardless).

## 2026-06-07 — Daily watch

**No new papers today.** Swept all 9 venues (web search across the standing queries; web_fetch on accepted-paper HTML). Re-fetched and fully re-grepped both **AsiaCCS 2026 Cycle 1 and Cycle 2** accepted lists this run — Cycle 1's only near-scope hit is "Original Sin of npm" (already in `excluded[]`); Cycle 2 has no Electron/desktop/Node.js-runtime papers (nearest items — container-escape detection, Windows-malware persistence, mixed-language compartments [FIDES], web-use-agent security — are all out of scope). USENIX Sec '26 Cycle 2 acceptances still not public (final papers due Jun 11; symposium Aug 12–14, 2026). CCS '26 accepted list still not public (only the ~19.5% between-cycle acceptance-rate stat is out). IEEE S&P '26 / NDSS '26 (fully grepped in prior runs) and ACSAC / RAID / ESORICS / DSN '26 surfaced no new in-scope hits. Every in-scope academic result that appeared is already in the ledger (DOM-tree type, Inspectron, COINDEF, Silent Spring, Mininode, HODOR, NodeShield, Bullseye, GASKET, GHunter, NodeMedic-FINE, XRCE/XGuard).

The 2026 Electron surface that searches returned is dominated by **CVE disclosures and industry write-ups**, not peer-reviewed top-venue papers: e.g., CVE-2026-34780 (context-isolation bypass via WebCodecs VideoFrame), CVE-2026-34769 (commandLineSwitches renderer switch injection), CVE-2026-34725 (dbgate-web stored XSS→RCE), CVE-2026-34781 (clipboard.readImage DoS), CVE-2026-42090 (Notesnook stored XSS→RCE), and the DeepChat openExternal-via-XSS RCE. These are real-world disclosures with no confirmed top-9-venue academic paper, so — consistent with prior out-of-venue handling — they are deliberately not added to `excluded[]` (which tracks watched-venue papers only). They remain useful as motivation/impact citations if the thesis wants fresh real-world examples.

Ledger unchanged: **12 in-scope / 9 excluded / 4 context**. Scoped commit attempted via `scripts/commit_and_push.sh` (commits only `electron_repo` into the parent repo; push fails offline — expected; user pushes from their own machine).

## 2026-06-06 — Daily watch

**No new papers today.** Swept all 9 venues (web search across the standing queries; web_fetch on accepted-paper HTML). The USENIX Sec '25 and '26 technical-session / accepted-paper pages are client-rendered and returned empty via web_fetch (no browser connected this run) → covered via targeted web search, as on 2026-06-05. USENIX Sec '26 Cycle 2 acceptances are not yet public (embargoed release tied to the Aug 12 symposium). IEEE S&P '26 (re-grepped with broad terms on 2026-06-05 → GASKET already added), NDSS '26, CCS '26 (accepted list still not public — only the between-cycle acceptance-rate stats are out, ~19.5%), and ACSAC / RAID / ESORICS / AsiaCCS / DSN '26 returned no new in-scope hits. Every in-scope result that surfaced is already in the ledger (DOM-tree type, Inspectron, COINDEF, Silent Spring, Mininode, HODOR, NodeShield, Bullseye, GASKET, GHunter, NodeMedic-FINE, XRCE/XGuard).

One novel candidate surfaced and was triaged out without ledgering: **"Internet-Scale Measurement of React2Shell Exploitation Using an Active Network Telescope"** (arXiv 2603.12300). It measures in-the-wild exploitation of *React2Shell* / **CVE-2025-55182** — a server-side React Server Components / Next.js Flight-payload deserialization RCE that executes under the Node.js runtime on servers. **Out of scope** (server-side web-framework RCE + network-telescope measurement; no desktop/Electron renderer / IPC / preload / contextIsolation angle) **and out of venue** (arXiv-only, no confirmed top-9 acceptance), so it is deliberately skipped and not added to `excluded[]` — consistent with prior out-of-venue skips (Dasty/WWW'24, "Learning to Triage Taint Flows"). If a future run finds it accepted at a watched venue, it will be re-triaged.

Ledger unchanged: **12 in-scope / 9 excluded / 4 context**. Scoped commit attempted via `scripts/commit_and_push.sh` (commits only `electron_repo` into the parent repo; push fails offline — expected; user pushes from their own machine).

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
