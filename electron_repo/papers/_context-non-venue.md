# Context papers — field-defining work NOT at the 9 watched venues

These are not from USENIX / S&P / NDSS / CCS / ACSAC / RAID / ESORICS / AsiaCCS / DSN, so they are deliberately excluded from the main index. But a related-work section on Electron-app vulnerabilities is incomplete without acknowledging them. Treat them as **context / motivation**, and be precise about their venue type (journal, industry talk, or preprint) when citing.

## Lost in Translation: Exploring the Risks of Web-to-Cross-platform Application Migration  ⭐ best-grounded Electron paper here
- **Authors:** Claudio Paloscia, Kostas Solomos, Mir Masood Ali, Jason Polakis (University of Illinois Chicago).
- **Venue / type:** ***Proceedings on Privacy Enhancing Technologies* 2025(4), pp. 24–39** — peer-reviewed (PoPETs/PETS), CC-BY-4.0, but **not one of the 9 watched venues**. Cite precisely; do not present as a top-4 security conference.
- **Links:** [PDF](https://petsymposium.org/popets/2025/popets-2025-0117.pdf) · DOI [10.56553/popets-2025-0117](https://doi.org/10.56553/popets-2025-0117) · artifact <https://github.com/masood/electron-wpt>
- **Full note:** [`popets2025-lost-in-translation.md`](popets2025-lost-in-translation.md) — full-text grounded.
- **Why it matters:** the peer-reviewed publication of the UIC MS thesis *"Differential Security Analysis of Cross-Platform Electron Applications"* listed further down, and a fourth discovery methodology for Electron alongside black-box config auditing (Inspectron), defenses (NDSS'23, COINDEF) and directed fuzzing (Buzz to Boom): **differential testing with Chrome as the oracle.** Retrofits Web Platform Tests to Electron and runs it across 8 Electron/Chromium pairs (12.0.2 → 31.3.0, 2021–2024), finding 8 mechanism divergences, 6 present in every version. Four are new: **all local files share one origin** (Chrome gives `file://` a null origin), **CORS exempts local contexts**, **CSP cannot govern `file://` at all**, and **WebViews enforce neither HTTPS upgrade nor mixed-content blocking.** Field study of 30 showcase apps: **25 load the main renderer from `file://`**, 3 of the 5 WebView users load local files into the WebView, and all 12 deployed CSPs are insufficient (Cacher's is written against the unsupported `file:` scheme and silently ignored; VS Code is the one app that does it right, via a custom `vscode://` scheme).
- **How to cite:** as the framework-semantics counterpart to application-level Electron work — and as the amplification factor behind every XSS→RCE advisory in this ledger: on a `file://`-loaded renderer a single XSS wins the whole local-file origin, not merely app-context execution. Note that **Electron declined the report as intended behaviour**, the same response Inspectron received, and that Mir Masood Ali is Inspectron's first author, so the two are one research programme rather than independent corroboration.

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

## Buzz to Boom: Detecting Message Progression Vulnerabilities in Electron Applications via Segmented Directed Fuzzing  ⭐ strongest promotion candidate
- **Authors:** Jianjia Yu, Zhengyu Liu, Ziyang Li, Yu Sun, Yinzhi Cao (Johns Hopkins University).
- **Venue / type:** **arXiv preprint, v1 submitted 22 Jul 2026 (arXiv:2607.20698, cs.CR).** No Comments/venue field on the arXiv page and no venue annotation in the full text → **not (yet) at any of the 9 watched venues.** Verify before citing as published.
- **Links:** https://arxiv.org/abs/2607.20698 · PDF https://arxiv.org/pdf/2607.20698
- **한 줄 요약 (KO):** Electron 앱의 프로세스 간 메시지 전달을 따라 공격자 입력이 여러 프로세스를 넘나들며 권한 있는 sink(예: OS 명령 실행)에 도달하는 새로운 취약점 부류(MPV)를 정의하고, 이를 자동 발견·익스플로잇하는 분절 지향 퍼징 프레임워크 Proton을 제안한 논문. **이 감시(watch)에서 지금까지 나온 것 중 논문 주제("Electron 앱 취약점 발견")와 가장 정확히 겹치는 연구.**
- **Why it matters (the single most thesis-central out-of-venue item so far):** Unlike the Node.js-runtime adjacency set in the main ledger (Silent Spring, GHunter, NodeMedic-FINE, …), this is a *direct* Electron **vulnerability-discovery** system — the exact contribution space of a thesis on discovering Electron-app vulnerabilities. It introduces a new bug class, **Message Progression Vulnerabilities (MPVs)**: attacker-controlled inputs that carry across processes via message passing and chain multiple steps (e.g. JS execution in one process → craft a new IPC message → command injection in a privileged process) to reach terminal sinks such as OS command execution. It explicitly frames prior academic Electron work as insufficient: "existing works on Electron security only study unsafe configurations and malicious DOM content … cannot detect or exploit these vulnerabilities that need … complex cross-process exploits via message passing" — i.e. it claims the gap left open by DOM-tree type (NDSS '23), Inspectron (USENIX '24), and COINDEF (S&P '25).
- **Method (from abstract + intro):** **Proton** decomposes end-to-end fuzzing into per-process **segments** along message-passing boundaries; each segment's goal is either (i) reaching a sink in the current process or (ii) propagating the payload to the next process (its output messages seed the next segment's corpus). An **agentic static-analysis** phase (LLM-driven) identifies candidate source→sink paths and segment boundaries and generates per-segment fuzzing harnesses + an input reconstructor + seeds; Proton then synthesizes and validates a full end-to-end exploit PoC against the whole app.
- **Key numbers (grounded in the paper text):** evaluated on **589 real-world Electron apps → 23 zero-day MPVs**, **22 escalate to full RCE / OS command execution** (including projects with **>50k GitHub stars**); responsibly disclosed → **13 acknowledgments, 11 fixes, 11 CVEs**, plus a **Vercel bug bounty for a vulnerability in Hyper**. Ablation: Proton finds **17 more** zero-days than end-to-end (non-segmented) fuzzing.
- **How to cite (draft, adapt after venue confirmation):** "Most prior academic work on Electron security targets unsafe framework configurations or malicious DOM content [DOM-tree type; Inspectron; COINDEF]. Yu et al. argue this misses *Message Progression Vulnerabilities* — bugs that only manifest through multi-step, cross-process message passing — and present Proton, a segmented directed fuzzer that discovered 23 zero-day MPVs (22 RCE, 11 CVEs) across 589 real Electron apps." **(KO)** 내 논문(취약점 발견) 관점에서는 가장 가까운 경쟁/보완 연구이므로 related work의 핵심 비교 대상. 이들이 남긴 gap(예: 정적 LLM 분석의 정확도, segment boundary 식별의 일반화, 비-command-injection sink로의 확장 등)을 내 기여의 차별점으로 삼을 여지가 큼. **단, arXiv 프리프린트이므로 게재 확정 전까지는 "preprint"로 표기.**
- **Caveats:** venue unconfirmed (arXiv-only as of this writing); the numbers above are grounded in the arXiv abstract (verbatim) and the intro/contributions of the full-text HTML, which were grepped rather than read end-to-end — re-verify exact figures and the evaluated security configuration against the PDF before citing.

## Unveiling the Invisible: Detection and Evaluation of Prototype Pollution Gadgets with Dynamic Taint Analysis (Dasty)
- **Authors:** Mikhail Shcherbakov, Paul Moosbrugger, Musard Balliu (KTH LangSec).
- **Venue / type:** **The Web Conference (WWW) 2024** — a strong venue, but **not** one of the nine watched.
- **Links:** https://arxiv.org/abs/2311.03919 · code https://github.com/KTH-LangSec/Dasty
- **Why it matters:** the missing middle link of the KTH prototype-pollution trilogy. *Silent Spring* (USENIX '23, `in_scope`) established that prototype pollution reaches RCE in Node.js; *GHunter* (USENIX '24, `in_scope`) found universal gadgets in the **runtime**; Dasty sits between them, finding gadgets in **third-party libraries** by dynamic taint analysis. Cite all three together in any prototype-pollution paragraph.
- **Caveats:** full text **not** read — recorded from the author page listing only. No numbers should be cited until the paper is read.

## Weaver: Fuzzing JavaScript Engines at the JavaScript-WebAssembly Boundary
- **Venue / type:** **UNVERIFIED.** Seen only as an arXiv PDF link (arXiv:2603.18789) inside a search-result list; neither the abstract nor the venue was checked.
- **Link:** https://arxiv.org/pdf/2603.18789
- **Why it matters:** same "fuzz the *boundary*, not the engine" framing as Favocado (NDSS '21) and COOPER (NDSS '22), one layer over — JS↔Wasm instead of JS↔C++.
- **⚠ ACTION NEXT RUN:** **check its venue.** If it landed at one of the nine, it is an `in_scope` candidate. Nothing about it should be cited until verified.

---

_If any of these is later accepted at a watched venue, move it into `papers/` as a full note and add an `in_scope` ledger entry._

**Buzz to Boom / Proton — promotion checkpoints:**

| List | Checked | Result |
|---|---|---|
| **CCS '26** | **2026-09-12** | ❌ **NOT accepted.** The full 187-title accepted-papers list was fetched from `sigsac.org/ccs/CCS2026/program/accepted-papers.html` and grepped for `buzz\|boom\|proton\|electron\|message progression\|segmented` — the only hit is *"Beyond the Buzzword: How do Professionals Understand and Translate Zero Trust?"*, unrelated. |
| USENIX Sec '26 Cycle 2 | — | not yet checked |
| NDSS '27 | — | list not published (news feed still at 18 Aug 2026) |
| S&P '27 | — | not yet checked |
