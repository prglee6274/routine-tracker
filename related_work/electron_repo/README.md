# electron_repo — Related-Work Tracker: Vulnerability Discovery in Electron Apps

A living literature base for a thesis on **discovering vulnerabilities in Electron-framework desktop applications**. It tracks academic papers on Electron-app security (and closely adjacent mechanisms) at the top security venues, summarizes each one in a fixed structure, and tells you how to cite it in a related-work section.

It is maintained in two modes:

1. **Backfill** — a one-time sweep of 2020 → present (done 2026-06-02).
2. **Daily watch** — a scheduled run that re-checks the venues, diffs against the ledger, and adds a note for anything new.

---

## Scope

**In scope.** Papers whose subject is the security / vulnerabilities of Electron apps, or of the mechanisms Electron relies on: `nodeIntegration`, `contextIsolation`, `sandbox`, preload / `contextBridge`, renderer↔main **IPC**, the `remote` module, Chromium Embedded Framework (CEF), WebView-based desktop apps, hybrid web/desktop apps, DOM-based / XSS→RCE escalation into local privileges, and npm/supply-chain issues *as they affect Electron or the Node.js runtime that powers it*.

**Out of scope.** Pure web-app XSS with no desktop/Electron angle; physics "electron" papers; mobile-only studies; generic Chromium browser bugs unrelated to embedded/desktop apps.

**Venues watched (9).**

| Tier | Venue | DBLP key |
|---|---|---|
| Top-4 | USENIX Security | `uss` |
| Top-4 | IEEE S&P (Oakland) | `sp` |
| Top-4 | NDSS | `ndss` |
| Top-4 | ACM CCS | `ccs` |
| 1.5 | ACSAC | `acsac` |
| 1.5 | RAID | `raid` |
| 1.5 | ESORICS | `esorics` |
| 1.5 | AsiaCCS | `asiaccs` |
| 1.5 | DSN | `dsn` |

---

## Headline finding from the backfill

The field is **niche and top-heavy**. Across all nine venues for 2020–2026, Electron-app vulnerability research lives almost entirely at **NDSS, CCS, USENIX Security, and IEEE S&P**. The 1.5-tier venues (ACSAC / RAID / ESORICS / AsiaCCS / DSN) are effectively empty on this exact topic — the only in-scope hit there is *Mininode* (RAID 2020), and even that targets server-side Node.js rather than Electron. **For a novelty claim, this is useful**: directly comparable prior work is a small, well-defined set.

---

## The papers (in scope)

| ID / note | Paper | Venue · Year | Scope | One-line |
|---|---|---|---|---|
| [`ndss2023-domtreetype`](papers/ndss2023-domtreetype.md) | A Security Study about Electron Applications and a Programming Methodology to Tame DOM Functionalities (Jin et al.) | NDSS · 2023 | PRIMARY | The anchor study of real Electron-app vulns (Teams, VS Code, …): 19 vulnerable apps found, 13 fixed; proposes the *DOM-tree type* defense. |
| [`ccs2022-xrce-xguard`](papers/ccs2022-xrce-xguard.md) | Understanding and Mitigating Remote Code Execution Vulnerabilities in Cross-platform Ecosystem (Xiao et al.) | CCS · 2022 | PRIMARY | Names/systematizes *XRCE* (XSS→local RCE) via a generic cross-platform model; ~75% of 640 apps exposed; builds *XGuard*. |
| [`usenixsec2024-inspectron`](papers/usenixsec2024-inspectron.md) | Rise of Inspectron: Automated Black-box Auditing of Cross-platform Electron Apps (Ali et al.) | USENIX Sec · 2024 | PRIMARY | Dynamic auditor of packaged Electron apps; 109 analyzed — nodeIntegration on in 49, sandbox off in 64, only 13/43 verify IPC sender. |
| [`sp2025-coindef`](papers/sp2025-coindef.md) | COINDEF: A Comprehensive Code Injection Defense for the Electron Framework (Yang et al.) | IEEE S&P · 2025 | PRIMARY | AST-structural-integrity defense inside V8; 20 apps / 79 attacks, 0 RCE in security-first mode, 3.96% startup overhead; beats DOMTYPING/XGuard. |
| [`usenixsec2023-silent-spring`](papers/usenixsec2023-silent-spring.md) | Silent Spring: Prototype Pollution Leads to RCE in Node.js (Shcherbakov et al.) | USENIX Sec · 2023 | ADJACENT | Prototype-pollution→RCE pipeline via CodeQL taint; 11 universal gadgets; 8 RCEs incl. Rocket.Chat (an Electron app). |
| [`raid2020-mininode`](papers/raid2020-mininode.md) | Mininode: Reducing the Attack Surface of Node.js Applications (Koishybayev & Kapravelos) | RAID · 2020 | ADJACENT | Static attack-surface reduction for Node.js; ~1.05M npm packages analyzed; removes ~90% of code; restricts fs/net in most apps. |

Out-of-venue but field-defining context (industry / journal / preprint) is tracked in [`papers/_context-non-venue.md`](papers/_context-non-venue.md). Papers that appeared at the watched venues but were ruled **out of scope** are recorded in the ledger's `excluded` list so the daily watch does not re-flag them.

---

## How each note is structured

Every file in `papers/` follows the same six-part template so they are directly reusable for writing:

1. **Problem, Gap & Hypothesis** — what gap the authors identify and what they set out to prove.
2. **Methodology** — the approach, techniques, and system design.
3. **Experiments / Evaluation Setup** — targets, dataset sizes, configurations, what was measured.
4. **Results / Key Findings** — the concrete numbers and takeaways.
5. **How to cite in Related Work** — 2–4 draft English sentences ready to adapt, plus a Korean note on how the paper positions relative to a vulnerability-*discovery* thesis (does it motivate the work? is it a defense to contrast? what gap does it leave open?).
6. **Caveats** — anything that could not be confirmed from the paper text.

Notes are written **in English with short Korean comments** (marked `(KO)`): the English is paste-ready for the paper; the Korean is for fast reading and for positioning the work against the thesis.

---

## Repository layout

```
electron_repo/
├── README.md                 ← this index
├── DAILY_UPDATE.md           ← what the daily watch does, and how to run/adjust it
├── CHANGELOG.md              ← log of backfill + each daily run
├── config/
│   └── sources.json          ← venues, DBLP keys, keywords, scope rules (machine-readable)
├── ledger/
│   └── seen_papers.json      ← every paper already triaged (in-scope, excluded, context) for the daily diff
└── papers/
    ├── ndss2023-domtreetype.md
    ├── ccs2022-xrce-xguard.md
    ├── usenixsec2024-inspectron.md
    ├── sp2025-coindef.md
    ├── usenixsec2023-silent-spring.md
    ├── raid2020-mininode.md
    └── _context-non-venue.md
```

---

## Pushing to GitHub

`electron_repo` lives inside the parent **`routine 생성`** git repo (the same repo that tracks your other projects), as an ordinary subfolder — it has **no separate `.git`**. The backfill is already committed there, scoped to this folder only.

Ongoing git works two ways:

- The **daily watch** commits *only* `electron_repo` changes into the parent repo, using an `electron_repo watch` author identity so your own git config is untouched. It cannot push (this run environment has no network).
- **You push** to GitHub from your own machine as part of your normal `routine 생성` workflow (`git push`), or run `scripts/commit_and_push.sh`, which commits just this folder and pushes if an `origin` remote exists.

If a run is ever interrupted and leaves a `.git/index.lock` in the parent repo, delete that file to unblock git.

---

## Verification status

Every in-scope paper's venue, year, authors, and links were verified against the venue's own page or an open-access PDF. Notes were grounded in the full PDF **except** `ccs2022-xrce-xguard.md`, where ACM was paywalled — that note is built from the abstract, the Georgia Tech write-up, and the COINDEF paper's description of XGuard, and says so at the top. Pull the full ACM PDF via institutional access to deepen it.

_Last backfill: 2026-06-02._
