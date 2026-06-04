# A Security Study about Electron Applications and a Programming Methodology to Tame DOM Functionalities

**Authors:** Zihao Jin; Shuo Chen; Yang Chen; Haixin Duan; Jianjun Chen; Jianping Wu (Microsoft Research; Tsinghua University)
**Venue / Year:** Network and Distributed System Security Symposium (NDSS) 2023, 27 Feb – 3 Mar, San Diego, CA, USA
**Links:** [paper](https://www.ndss-symposium.org/ndss-paper/a-security-study-about-electron-applications-and-a-programming-methodology-to-tame-dom-functionalities/) · [PDF](https://www.ndss-symposium.org/wp-content/uploads/2023-305-paper.pdf) (mirror: https://www.microsoft.com/en-us/research/wp-content/uploads/2022/12/domtreetype-ndss.pdf) · DOI: 10.14722/ndss.2023.24305 · ISBN 1-891562-83-5
**Scope tag:** PRIMARY
**Relation to a thesis on discovering Electron-app vulnerabilities (one line):** This is the foundational empirical study of payload-injection (XSS / scriptless) vulnerabilities in real-world Electron apps and the source of the "DOM-tree type" defense that later work (e.g., COINDEF) calls "DOMTYPING" and contrasts against.

> **한 줄 요약 (KO):** 실제 Electron 앱(Teams, VS Code 등) 19개에서 페이로드 인젝션 취약점을 발견하고, DOM 트리가 의도하지 않은 형태로 변형되는 것을 "타입 위반"으로 잡아내는 DOM-tree type 방어 기법을 Electron 플랫폼에 직접 구현한 연구.

## 1. Problem, Gap & Hypothesis

The paper argues that Electron inherits decades-old HTML+JS injection risks ("XSS" + "scriptless attacks", jointly called *payload injection bugs*) into the desktop realm, but with a twist: same-origin-policy boundaries usually do not apply, code/data read from local input sources and run with local-machine privilege, and apps are more complex than websites or mobile apps (§I, §II). The authors contend that the conventional framing — treating these as "sanitization errors" to be fixed by enumerating all bad inputs — is fundamentally error-prone, because it requires programmers to "anticipate the unexpected" (§I, §III-A, §IV). Their hypothesis: secure programming should instead let programmers *specify their intentions* (the set of DOM trees the app expects), so any exploit becomes a *gain-of-function DOM-tree mutation* caught as a **type violation**. The idea is explicitly inspired by "types-from-data" (Petricek/Syme, PLDI 2016, ref [21]) and conceptually by browser Trusted Types (ref [9]) (§I, §IV).

> (KO) 핵심 갭은 "비의도(non-intention)를 일일이 막는" 새니타이저 방식의 한계. 가설은 "의도(intention)를 타입으로 명시"하면 익스플로잇이 타입 위반으로 자동 검출된다는 것. 정적 버그 탐지가 아니라 런타임 타입 강제(enforcement)로 패러다임을 전환한다는 점이 핵심.

## 2. Methodology

Two parts: (a) an empirical vulnerability study, and (b) a defense methodology built into Electron.

**Study (§III).** Two rounds. Round 1: 12 apps with source-code access were manually inspected and tested; 6 were found exploitable (Microsoft Teams, GraSSHopper SSH client, VS Code, Antares SQL client, Homura RSS reader, OhHai Browser). Round 2: a semi-automatic approach over 70 more apps from Electron's official site, using a modified Electron with a hook on the HTML parser that records every string being parsed (to surface raw-HTML injection points); navigation through app features was manual.

**Defense — DOM-tree type (§IV–§V).** A *DOM-tree type* expresses the (typically infinite) set of DOM trees the app intends to see; it is itself tree-structured, made of *shadow elements* with four fields: children (an unordered, deduplicated set), an identifier (tag name + `id`), attributes (each holding a *set* of values — URL attributes reduce to sets of origins, script attributes to sets of JS token sequences), and style properties (string sets, origin sets, numeric ranges). Text nodes are excluded except inside `<script>`/`<style>`. 29 of 367 layout-dependent style properties (width, height, margins, transform, etc.) are excluded.
Two platform modules are added to Electron:
- **TypeBuilder** — a dev utility that observes DOM-tree changes across test runs and grows the type by union (only adds, never removes); the type "converges" when more testing adds nothing. Two manual generalizations are offered: *attribute-value-wildcarding* (`*`/`?`) and *subtree-flattening* (for "structure-agnostic subtrees" like markdown/article content areas, equivalent to a sanitizer whitelist).
- **TypeEnforcer** — at runtime rejects any mutation introducing a missing element/attribute/value, raising an exception.
A shared **DOM Interceptor** hooks five C++ chokepoint methods in Chromium's Blink engine (`SetComputedStyle`, `InsertBefore`/`AppendChild`/`ReplaceChild`, `WillModifyAttribute`). A key insight (§V) is that `MutationObserver` is insufficient because *disconnected elements* can trigger persistent effects (network/file requests, event-handler registration, DNS prefetch) *before* type-checking; the authors enumerate which of 121 `HTMLElement` descendant classes (53 override one of five virtual methods) can do this, and **defer** those persistent effects until an element is connected to the DOM tree and checked. They claim this deferral mechanism was missing in prior DOM-inspection techniques, which they could bypass. The system reuses Blink's HTML/CSS parsers and V8's JS tokenizer, avoiding any custom sub-grammar parser of their own.

> (KO) 방어의 핵심은 (1) DOM 변경의 모든 chokepoint(Blink C++ 5개 메서드)를 가로채고, (2) DOM 트리에 "연결되지 않은(disconnected)" 요소가 타입 검사 전에 일으키는 부수효과를 연결 시점까지 *지연(defer)* 시키는 것. 이 deferral이 기존 기법(MutationObserver, PoliDOM 등)을 우회할 수 있었던 빈틈을 메운다고 주장. 자체 파서를 만들지 않고 Blink/V8 파서를 재사용해 파싱 불일치 자체를 제거한 점이 설계상 장점.

## 3. Experiments / Evaluation Setup

Implemented on **Electron 12.0.0 (Chromium 89)**, mostly C++ with a TypeScript interface adding `SetDOMTreeType` / `SetTypeEnforcerMode` / `OutputDOMTreeType` to Electron's `webFrameMain` (§VII). Validity/security evaluation ran on **18 apps** (Table VI): VS Code, GraSSHopper, Antares, Homura, OhHai Browser, plus all 13 second-round apps. Microsoft Teams was excluded because it runs on a proprietary Electron variant. Extensibility was tested on **6 VS Code extensions** (Table VII: a dummy extension, Golang/TypeScript/Mojom syntax highlighters, Todo Tree, FTP Simple). Performance used the **Speedometer 2.0** benchmark (16 to-do-list app implementations × 3 action types), firing 100 add + 100 finish + 100 delete actions at frequencies from 10 to 100 actions/sec; each reported completion time averages 300×16 = 4800 measurements, compared against unmodified Electron of the same version (§VII-B).

> (KO) 평가 대상은 발견한 취약 앱 그 자체(총 18개) + VS Code 확장 6개. 성능은 Speedometer 2.0으로 측정. 단, Teams는 독자(proprietary) Electron이라 방어 평가에서 제외 — 이 점은 향후 인용 시 주의할 만함.

## 4. Results / Key Findings

- **Vulnerabilities found: 19 apps total** (6 in round 1 + 13 in round 2). Vendors **confirmed or fixed 13** of the 19 (§I, §VII-C). At writing time, Antares, Tess, Altair, Blockbench, Advanced REST Client were confirmed-and-fixed; Microsoft Teams, GraSSHopper, Homura, Jukeboks, DeckMaster, Poddycast, Boost Note, Appium Desktop had confirmed and were fixing (§VII-C).
- Concrete exploit examples (§III): Teams — (1) user-tracking via a CSS `background-image: url(...)` smuggled past both independent client-side and server-side sanitizers, (2) fake CEO/CTO chat messages via a post-processing module re-assigning a `value` attribute to `class` (`CodeMirror-fullscreen`, z-index 9, position fixed). GraSSHopper — arbitrary script execution via selected text or hostname interpreted as a file path and assigned to `innerHTML`, including a hardcoded-nonce CSP bypass. VS Code — IP-leak via external images rendered from Markdown in hover popups (URL extraction and code-comment rendering). Antares/Homura/OhHai Browser — fully *unsanitized paths* (DB table names, RSS contents, page titles/bookmarks rendered as HTML).
- The 13 second-round apps (Table I) were all *unsanitized-path* cases; injection points included filenames, podcast/RSS titles, MIME types, HTTP headers, error messages, file paths, markdown, and DB records.
- **Security effectiveness:** TypeEnforcer caught/thwarted every exploit; Appendix C lists the exact DOM-tree-type violation (e.g., the GraSSHopper text-selection attack adds an extra `iframe` at a specific path). No normal functionality was broken under enforcer mode.
- **Programmer effort was small** (Table VI): most apps needed only a few attribute wildcards or one subtree-flatten; several needed none. VS Code extension type complexity grew *linearly* with installed extensions.
- **Performance overhead negligible:** at a realistic ~12.5 actions/sec the slowdown was 0.287%; at the "aggressive" 10 actions/sec load it was 0.001%. Larger slowdowns only appeared under unrealistically high firing rates (stress test).

> (KO) 숫자 요약: 발견 19개, 확인/수정 13개. 방어는 발견한 모든 익스플로잇을 차단했고 정상 기능 손상 없음. 프로그래머 수작업은 적음(와일드카드/플래튼 약간). 오버헤드는 현실 부하에서 사실상 0%. 단, 성능은 자체 모듈이 Blink 외부에 있어 최적은 아니라고 저자 스스로 인정.

## 5. How to cite in Related Work

> Jin et al. (NDSS 2023) conducted the first systematic security study of real-world Electron desktop applications, manually auditing 12 source-available apps and semi-automatically scanning 70 more, and reported 19 vulnerable applications (13 confirmed or fixed by vendors) spanning flagship products such as Microsoft Teams and Visual Studio Code. Rather than treating these as sanitization errors, they reframed the problem as *gain-of-function DOM-tree mutations* and introduced the *DOM-tree type* — a typed specification of the DOM trees an app intends to produce — enforced inside Chromium's Blink engine by a TypeBuilder/TypeEnforcer pair that hooks five DOM chokepoints and defers the persistent effects of disconnected elements until they are checked. Their enforcer blocked every exploit they discovered with negligible (<0.3%) runtime overhead under realistic loads.

> (KO) 포지셔닝: 이 논문은 *우리(취약점 발견) 연구의 직접적인 동기*다 — Electron 앱이 실제로 취약하다는 것을 경험적으로 입증했기 때문. 동시에 이 논문은 **방어 기법(DOM-tree type)** 이기도 하므로, "발견" 중심 논제에서는 (a) 발견 방법론(HTML 파서 후킹 기반 semi-automatic 탐색)을 벤치마크/베이스라인으로 인용하고, (b) 남은 갭을 강조하는 게 좋다. 남은 갭: 이 방어는 *DOM 변경을 동반하지 않는* 공격(`eval(user_str)`, top-level navigation/client-side-redirect, prototype pollution)은 못 막는다고 §VI에서 명시 — 바로 이 지점을 COINDEF(S&P 2025)가 파고든다. 발견 논제라면 "어떤 클래스의 취약점이 이 방어로 안 잡히는가, 따라서 어떻게 새로 발견할 것인가"로 연결 가능.

## 6. Caveats / what I could not confirm from the text

- The 19-vs-13 framing: I confirmed "19 vulnerable apps" and "confirmed or fixed 13" in the abstract/§I/§VII-C. The breakdown of *which specific 13* were "confirmed-and-fixed vs. confirmed-and-fixing" is given but the two states overlap textually; treat "13 fixed" loosely — the precise wording is "confirmed or fixed 13 of them."
- I read the full paper text including appendices (BNF, excluded style properties, violation table). I did **not** independently verify the anonymized code repo (ref [35]) or exploit-video site (ref [36]) — those links were anonymized for review.
- Teams LoC figures (235 kLoC thin layer wrapping 2170 kLoC web client) and "367 style properties / 29 excluded" / "121 descendant classes / 53 override" are quoted directly from the text but I could not cross-check them against source.
- Exact per-app slowdown beyond the two cited points (0.287% at 12.5/s; 0.001% at 10/s) is only given as a table of completion times (Fig. 6); I did not recompute every cell.
- The paper does not assign CVE numbers in the text I read; COINDEF (Paper B) later attaches specific CVEs to several of the same apps.
