# SandDriller: A Fully-Automated Approach for Testing Language-Based JavaScript Sandboxes

**Authors:** Abdullah AlHamdan, Cristian-Alexandru Staicu (both CISPA Helmholtz Center for Information Security)
**Venue / Year:** 32nd USENIX Security Symposium (USENIX Security '23), Anaheim, CA, August 2023
**Links:** [paper page](https://www.usenix.org/conference/usenixsecurity23/presentation/alhamdan) · [PDF (USENIX, free)](https://www.usenix.org/system/files/usenixsecurity23-alhamdan_1.pdf) · [author-hosted PDF](https://www.staicu.org/publications/usenixSec2023-SandDriller.pdf) · DOI: n/a (USENIX open access)
**Scope tag:** ADJACENT

**Relation to a thesis on discovering Electron-app vulnerabilities (one line):** This is the closest methodological ancestor in the ledger to an *automated discovery* technique for isolation-boundary bugs — it treats a JavaScript isolation boundary as a testable artifact and synthesises working escapes, which is exactly what one wants to do to Electron's `contextIsolation` / `contextBridge` boundary.

> **한 줄 요약 (KO):** vm2·ses·realms-shim 같은 "언어 기반 JavaScript 샌드박스"를 자동으로 깨뜨리는 최초의 동적 분석 도구로, 프로토타입 체인을 타고 샌드박스 밖으로 새어 나오는 참조(foreign reference)를 오라클로 탐지해 8개의 제로데이 탈출 취약점을 자동 합성했다.

---

## 1. Problem, Gap & Hypothesis

**Problem.** Language-based isolation — running untrusted JavaScript in the same runtime as trusted host code, with membranes/proxies interposed instead of a separate process — is the cheap way to confine third-party code. It was pioneered in the browser (Google Caja, Douglas Crockford's ADsafe) for web mashups, largely abandoned there, and then revived *outside* the browser: Cloudflare for resource sharing, TripAdvisor for server-side rendering, Embark and Agoric for blockchain, Moddable for IoT, Box.js for malware analysis. `vm2` alone had millions of weekly downloads at the time of writing. A bug in the containment logic means untrusted guest code reaches host builtins and, from there, `require('child_process')` — i.e. RCE.

**Gap.** Prior work on sandbox correctness is *static/verification*-shaped: Politz et al.'s type-based analysis of ADsafe, Taly et al.'s reference-monitor definitions, Maffeis et al.'s authority safety, Finifter et al. on root-prototype methods. The authors argue these cannot keep up with modern sandboxes, for two concrete reasons: (i) modern sandboxes build on Node.js's `vm` module and interpose via the ES6 `Proxy` API, which the older analyses predate and which defeats static reasoning; (ii) the bugs live in *obscure, newly-introduced language features* (their motivating CVE-2021-23449 turns on dynamic `import()`, added in ES2015), so finding them statically would require modelling the whole of JavaScript plus Node's extensions — beyond existing static analyses for JS. Meanwhile the fuzzing literature for JS *engines* uses crash oracles, which are useless here: the containment logic is written in JavaScript, so a successful escape produces no crash.

**Hypothesis.** Sandbox escapes have a single observable structural signature — a **foreign reference**, i.e. a reference reachable from inside the sandbox whose prototype chain terminates outside it. If you interpose a check on every reference crossing the host/guest boundary and walk its transitive closure, you can detect the precondition for an escape *before* an escape is written, and then synthesise the escape automatically. Corollary: an ordinary, benign code corpus (conformance tests) is a sufficient input, because benign code already exercises the obscure language corners where these leaks live.

> **(KO)** 핵심 통찰: "샌드박스 탈출"은 결국 프로토타입 체인의 루트가 샌드박스 바깥을 가리키는 참조(foreign reference) 하나로 환원된다는 것. 그래서 크래시 오라클이 아니라 *참조의 프로토타입 체인을 순회하는* 도메인 특화 오라클이 필요했고, 이 덕분에 악성 입력을 만들 필요 없이 평범한 ECMAScript 적합성 테스트 코퍼스만으로도 탈출을 찾아낼 수 있었다.

## 2. Methodology

Two halves: an empirical study (§2) that establishes what these sandboxes are *supposed* to do, then a testing pipeline (§3) that checks whether they do it.

**The study.** The authors read documentation, studied every previously reported breakout and its fix, set the sandboxes up locally, and audited source. From this they distil **four security objectives**:

- **SO1** — prevent side effects in the runtime (no writes to the global scope / intrinsics; prototype pollution is the general form of this failure).
- **SO2** — restrict access to privileged operations (e.g. `require`), modulo an explicit list of **endowments** (shared references the user deliberately grants).
- **SO3** — prevent blocking the host's event loop (infinite loops).
- **SO4** — prevent crashing the host process (e.g. memory exhaustion).

They split the population into **runtime-based** sandboxes (separate process/worker/V8 Isolate: BreakApp, jailed, TreeHouse, deno-vm, isolated-vm) and **language-based** ones (vm2, ses, realms-shim, near-membrane, safe-eval, notevil, SandTrap, AdSafe, Caja). Key finding of the study half: language-based sandboxes mostly do not even *target* SO3/SO4, and where they do, the control is bypassable (notevil's iteration cap is side-stepped with higher-order functions over large arrays).

**SANDDRILLER's pipeline** (≈2,000 LoC JavaScript; `esprima` for instrumentation, `deltajs` for minimisation, Puppeteer for client-side sandboxes, AddressSanitizer as a memory-violation oracle):

1. **Instrumentor** — rewrites the seed program so that every construct capable of introducing a *new* reference into the sandbox is checked. The three vectors it targets, derived from real exploits, are (i) return values of calls to host methods, (ii) thrown exceptions, (iii) callback arguments. E.g. `foo()` becomes `(let temp = foo() & checkReference(temp) & foo)`; every `try`/`catch` is wrapped.
2. **Oracles** — for each intercepted reference, walk the transitive closure looking for signs it is foreign, points to a privileged operation, or carries the value of a global flag the harness planted outside the sandbox.
3. **Exploitation** — on a hit, *confirm* by actually attempting a write outside the sandbox or an invocation of a privileged operation. (This is why the tool has **no false positives by construction**: every alert corresponds to an executed violation.)
4. **Variant generator** — recombines seed programs with ingredients harvested from known breakout exploits, up to five variants per seed (the JS-engine-fuzzing trick, applied to sandboxes).
5. **Minimisation** — delta debugging to a compact PoC; the authors note `deltajs` frequently gets stuck and needed manual delta debugging, and root-cause grouping is manual.

> **(KO)** 계측 대상이 "함수 반환값 / 예외 / 콜백 인자" 세 곳으로 좁혀진 점이 중요하다 — 실제 CVE들을 역공학해서 뽑아낸 목록이다. Electron으로 옮겨 생각하면 `contextBridge.exposeInMainWorld`로 노출된 함수의 **반환값과 던져진 예외**가 정확히 같은 세 통로에 해당한다. 그리고 "탐지 후 실제로 익스플로잇을 시도해 확인"하는 구조라서 오탐이 원리적으로 0이라는 점도 방법론적으로 배울 만하다.

## 3. Experiments / Evaluation Setup

- **Targets:** six language-based sandboxes that could be driven without writing a policy — `vm2`, `realms-shim`, `safe-eval`, `near-membrane`, `AdSafe`, `ses`. Excluded: SandTrap and Mir (require security policies), Caja (discontinued early 2022, isolation component undocumented). Additional manual findings cover `isolated-vm`, `jailed`, `notevil`, `SandTrap` and Node's own `vm` module.
- **Runtimes:** three Node.js versions — **14.15 (LTS), 15.12, 16.12** — because the authors observed that exploits are version-specific (the vm2 `process.removeListener` PoC works on 14.15 but not 16.12).
- **Corpus:** **46,606 seed programs** = **41,034** ECMAScript conformance tests (Test262) + **5,572** V8 unit tests, plus up to 5 generated variants each.
- **Infrastructure:** process pool of 16, 10 s timeout per test; server with 64× Intel Xeon E5-4650L @ 2.60 GHz, 768 GB RAM, Debian GNU/Linux 10.
- **Measured:** per (sandbox × corpus × Node version), the counts of tests that ran without error / runtime error / timeout / **security error** / **hard crash** / **memory corruption**; plus the distribution of oracle checks per test and test execution time.
- **Total effort:** **17.27 hours** of running time, **>3 billion oracle checks**.

> **(KO)** 평가 설계에서 눈여겨볼 점 두 가지. (1) 공격 코퍼스를 따로 만들지 않고 **Test262 + V8 유닛테스트**라는 "정상 코드"를 씨앗으로 썼다 — 취약점 발견 논문에서 입력 확보 비용을 없애는 좋은 전략. (2) Node.js 버전 3개를 교차 검증했는데, 같은 익스플로잇이 버전에 따라 되고 안 되는 사례가 실제로 나왔다. Electron은 Node/Chromium 버전이 릴리스마다 바뀌므로 이 교훈이 그대로 적용된다.

## 4. Results / Key Findings

- **115,085 security violations** and **48 hard crashes** observed overall, affecting **five of the six** sandboxes tested. After manual root-cause grouping the authors report **13 distinct security problems**; **12 confirmed zero-day security issues**, of which **8 unique zero-day sandbox breakouts** plus **2 crashes** are the headline claim; **8 security advisories** were assigned, most rated *critical*. At time of writing **8 were fixed** and **one sandbox was marked deprecated** in response.
- **Per-sandbox outcome (Table 2, summed over both corpora, all Node versions, incl. variants).** Security errors: `AdSafe` 45,287 (44,441 ECMA + 846 V8); `near-membrane` 39,570; `safe-eval` 35,536; `realms-shim` 115; `vm2` 82; **`ses` 0**. Hard crashes: `vm2` 22, `safe-eval` 22, `near-membrane` 4, others 0. Memory-corruption hits are 6 per sandbox on ECMA and 0 on V8 — an artifact of `allocation-limit.js` tripping AddressSanitizer, which the authors use to argue crash/memory oracles are **too coarse-grained** for this problem.
- **`ses` is the only sandbox not broken**, and it also has the highest number of runtime errors and timeouts. The authors attribute this to **freezing the intrinsics** — better isolation at the cost of rejecting legitimate code. That trade-off is stated explicitly.
- **AdSafe, near-membrane and safe-eval fail trivially** — e.g. using `this` as a foreign reference. For AdSafe the diagnosis is dependency rot: it relies on JSLint to perform static transformations (removing direct prototype accesses) that **recent JSLint versions no longer perform**, silently breaking the sandbox's invariant.
- **A bug in Node.js's own `vm` module** (Figure 5), affecting all three Node versions and therefore most of the sandboxes built on it: an infinite-recursion exception acts as a foreign reference — but only if a seemingly superfluous `new Error().stack` line is present, which changes the `try`/`catch` block from executing once to **498 times** in their setup. Traced to a 2019 Node commit. The authors worked with the Node.js team to make the "the vm module is not a security mechanism" warning more explicit in the documentation.
- **Confirmed advisories (Table 4):** `isolated-vm` **CVE-2021-21413** (capability leak; reported 8 Feb 2021, fixed 12 Feb 2021 — the authors believe this is the *first published vulnerability report for a runtime-based JavaScript sandbox*); `vm2` **CVE-2021-23449** (dynamic `import` + custom stack traces; reported 15 Sep 2021, fixed 12 Oct 2021); `vm2` **CVE-2021-23555** (`vm`'s `stack` property; reported 25 Nov 2021, fixed 8 Feb 2022); `vm2` issue #285 (custom `toString()` on listener objects, same-day fix); `realms-shim` **CVE-2021-23594** and **CVE-2021-23543** (both reported 10 Dec 2021, **no fix**); `SandTrap` **GHSA-xx7r-mw56-3q2h** (reported 22 Sep 2021, fixed 11 Nov 2021); `jailed` **CVE-2022-23923** (direct access to powerful builtins, **no fix**); `notevil` **CVE-2021-23771** (property-name restriction bypass, **no fix**).
- **The variant generator helps but inflates**: security violations and hard crashes both rise with variants, and the authors warn part of that rise is an artifact (a violating seed's variants tend to violate too — bounded at ~5× — though `vm2` on Node 16.12 exceeds that bound). Both corpora independently find bugs, so the approach is not corpus-specific.
- **Oracle-check count is a poor proxy for effectiveness**: `realms-shim` shows few checks yet yields important breakouts.
- **Fixes are usability-hostile.** The maintainers' response to the `import`-based escape was to *disallow `import` inside the sandbox*; the stack-trace escapes push toward disabling custom stack traces. Benign code using those APIs is collateral damage.

> **(KO)** 숫자보다 중요한 결론 세 가지. (1) **가장 안전했던 `ses`는 "가장 많이 깨진 사용성"의 대가로 그 안전을 샀다** — 격리 강도와 호환성은 정면충돌한다. (2) **AdSafe의 실패 원인이 외부 의존성(JSLint)의 조용한 동작 변경**이라는 점은, 설정 기반 방어(Electron의 `webPreferences`도 마찬가지)가 주변 환경이 바뀌면 소리 없이 무력화된다는 일반 교훈이다. (3) **Node.js `vm` 모듈 자체의 버그**가 그 위에 쌓인 샌드박스 다수를 한꺼번에 무너뜨렸다 — 런타임 하부의 결함이 상부 격리 계층 전체로 전파되는 구조.

## 5. How to cite in Related Work

> Automated discovery of isolation-boundary failures in JavaScript has so far targeted general-purpose sandboxes rather than desktop application frameworks. AlHamdan and Staicu's SANDDRILLER [ref] is the first dynamic-analysis approach for detecting sandbox-escape vulnerabilities in language-based JavaScript sandboxes; its central abstraction is the *foreign reference* — a reference reachable from guest code whose prototype chain terminates in the host — which it detects by interposing oracle checks on every value returned, thrown, or passed to a callback across the host/guest boundary, and then confirms by synthesising a working escape. Running 46,606 benign seed programs from Test262 and the V8 unit tests against six sandboxes on three Node.js versions, it reported 13 distinct security problems and 8 unique zero-day breakouts, including a defect in Node.js's own `vm` module that propagates to every sandbox built on it. Electron's `contextIsolation` is a language-based isolation boundary of exactly this kind — separate V8 contexts bridged by `contextBridge` — yet no analogous automated escape-finding technique has been applied to it; existing Electron work either audits configuration statically [Inspectron] or defends a known injection path [COINDEF] rather than searching for boundary escapes.

> **(KO)** 관련연구에서의 위치: 이 논문은 **"방어"가 아니라 "발견"** 쪽 계보에 속하며, 그래서 본 논문(취약점 발견 학위논문)의 직접적인 방법론적 선례다. 인용 각도는 세 가지가 있다.
> - **동기 부여용**: "언어 기반 격리는 자동화된 탐색 앞에서 반복적으로 무너진다"는 실증 근거. Electron의 contextIsolation도 같은 계열의 격리다.
> - **방법론 차용**: foreign reference 오라클 = "프로토타입 체인 루트가 경계 밖을 가리키는가"라는 판정 기준. Electron에서는 `contextBridge`로 넘어온 객체·반환값·예외가 privileged preload world의 프로토타입에 닿는지를 같은 방식으로 검사할 수 있다. 실제로 Electron **CVE-2026-70610**(contextBridge 객체 복사가 프로토타입 setter를 존중)과 **CVE-2026-70601**(`Function.prototype.bind` 하이재킹으로 context isolation 우회)은 SANDDRILLER의 오라클이 그대로 겨냥하는 형태의 버그다 — 즉 "이 기법을 Electron에 이식하면 실제로 있는 종류의 버그를 잡는다"는 논거를 CVE로 뒷받침할 수 있다.
> - **남긴 빈틈(= 본 논문의 자리)**: ① 평가 대상이 **npm 샌드박스 라이브러리**일 뿐 데스크톱 앱 프레임워크가 아니다. ② `vm2`/`ses` 같은 **단일 프로세스 내 언어 격리**만 다루고, Electron의 **renderer↔main IPC라는 프로세스 간 경계**는 다루지 않는다. ③ 정책을 요구하는 샌드박스(SandTrap, Mir)는 아예 평가에서 제외했는데, Electron 앱은 바로 그 "앱마다 다른 정책(preload에서 무엇을 노출할지)"이 본질이다. ④ 저자 스스로 "runtime-based 샌드박스로도 확장 가능할 것"이라고만 추측하고 끝냈다. ①~④가 전부 Electron 방향으로 열린 문이다.

## 6. Caveats / what I could not confirm from the text

- **Grounding.** Full author-hosted PDF read: abstract, §1, §2 (incl. Table 1 caption and the vm-module discussion), §3.1, §3.5, §4 setup, §4.1 with Table 2, Table 4, §4.3 Discussion, and §5 Related Work. **Not read in detail:** §3.2–3.4 (sandbox runner, variant generator, outcome checking) beyond their summaries, the full body of Table 3 (only the Node 14.15 block was read), Figures 3–4 (distributions, image-only in the text extraction), and Appendix A / Table 5 (the complete list of prior vulnerabilities per sandbox).
- **Table 1's per-sandbox objective matrix (which sandbox targets which SO, and the weekly-download figures as of 9 Oct 2022) is rendered as symbols in the extracted text and could not be read reliably** — do not cite specific per-sandbox SO coverage or download counts from this note without re-opening the PDF.
- **The Table 2 per-sandbox sums above are my own additions of the ECMA and V8 rows as extracted**; the extraction misaligns the `safe-eval` / `ses` / `near-membrane` row labels (the sandbox name is printed between its two data rows), so I have assigned rows by position. The totals are self-consistent with the paper's prose (5 of 6 sandboxes broken; `ses` at zero; AdSafe/near-membrane/safe-eval "by far the highest"), but **verify row assignment against the PDF before quoting a specific per-sandbox number**.
- The paper reports both "**13** distinct security problems" (§1, after grouping) and "**12** confirmed zero-day security issues" and "**8** unique zero-day sandbox breakout vulnerabilities and two crashes" (abstract). These are different countings (reported vs. confirmed vs. unique breakouts), not a contradiction, but cite the one you mean.
- **No Electron, CEF, or desktop-application evaluation appears anywhere in the paper.** The connection drawn in §5 above is mine, not the authors'.
- Whether SANDDRILLER's artifact is publicly available was not established from the sections read (a USENIX '23 artifact appendix exists for the conference; I did not check it for this paper).
